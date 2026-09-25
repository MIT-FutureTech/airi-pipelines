import logging
import statistics
from collections import Counter
from collections.abc import Sequence
from datetime import UTC, datetime
from pathlib import Path

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings

from agora_screening.compare import (
    CID_ARTEFACT_THRESHOLD,
    IN_SCOPE_THRESHOLD,
    InvarianceGroup,
    ScoredDocument,
    corrupt_extractions,
    distribution,
    invariance_groups,
)
from agora_screening.corpus import DocumentRecord, load_oecd_corpus
from agora_screening.results import PipelineStage, load, load_stage, save, stage_dir
from agora_screening.score import ScoreResult, ScoreStatus
from agora_screening.settings import DEFAULT_CORPUS_PATH, AgoraScreeningSettings

logger = logging.getLogger(__name__)

REPORT_FILENAME = "report.md"
MANIFEST_FILENAME = "run.json"
SHORTLIST_SIZE = 10
EXAMPLES = 5


class RunManifest(BaseModel, frozen=True):
    """What a scoring run was asked to do, written before the first LLM call.

    A report regenerated later can then say which model, rubric and text budget
    produced the results it describes, rather than guessing from the files.
    """

    started_at: datetime
    selected: int
    configuration: dict[str, str]


class ShortlistEntry(BaseModel, frozen=True):
    readable_id: str
    score: int
    name_english: str
    jurisdiction: str


class RunSummary(BaseModel, frozen=True):
    """Everything the report states, computed once so it can be tested directly."""

    generated_at: datetime
    output_dir: Path
    manifest: RunManifest | None
    corpus_size: int
    with_text: int
    results_total: int
    written_this_run: int | None
    status_counts: dict[str, int]
    distribution: dict[str, int]
    mean_score: float | None
    median_score: float | None
    in_scope: int
    shortlist: list[ShortlistEntry]
    title_checks: dict[str, int]
    truncated: int
    chars_sent: int
    original_chars: int
    input_tokens: int
    output_tokens: int
    results_without_usage: int
    corrupt: list[tuple[str, float, int]]
    invariance: list[InvarianceGroup]


def manifest_path(output_dir: Path) -> Path:
    return output_dir / MANIFEST_FILENAME


def write_manifest(
    settings: AgoraScreeningSettings, *, selected: int, started_at: datetime
) -> RunManifest:
    manifest = RunManifest(
        started_at=started_at,
        selected=selected,
        configuration={key: str(value) for key, value in settings.model_dump().items()},
    )
    save(manifest_path(settings.output_dir), manifest)
    return manifest


def load_manifest(output_dir: Path) -> RunManifest | None:
    path = manifest_path(output_dir)
    if not path.exists():
        return None
    return load(path, RunManifest)


def _as_scored(result: ScoreResult) -> ScoredDocument:
    return ScoredDocument(
        readable_id=result.readable_id,
        score=result.assessment.scope_score if result.assessment else None,
        title_check=result.title_check.value if result.title_check else "",
    )


def _written_since(output_dir: Path, started_at: datetime) -> int:
    threshold = started_at.timestamp() - 1
    return sum(
        path.stat().st_mtime >= threshold
        for path in stage_dir(output_dir, PipelineStage.SCORE).glob("*.json")
    )


def _shortlist(
    results: Sequence[ScoreResult], corpus_by_id: dict[str, DocumentRecord]
) -> list[ShortlistEntry]:
    assessed = [
        (result, result.assessment)
        for result in results
        if result.assessment is not None
    ]
    assessed.sort(key=lambda pair: (-pair[1].scope_score, pair[0].readable_id))
    return [
        ShortlistEntry(
            readable_id=result.readable_id,
            score=assessment.scope_score,
            name_english=assessment.name_english,
            jurisdiction=corpus_by_id[result.readable_id].jurisdiction,
        )
        for result, assessment in assessed[:SHORTLIST_SIZE]
    ]


def summarise(
    *,
    output_dir: Path,
    corpus: Sequence[DocumentRecord],
    min_chars: int,
    manifest: RunManifest | None,
    generated_at: datetime,
) -> RunSummary:
    """Read every result under the output directory and describe the run.

    The summary covers all results on disk, not only those written in the
    latest invocation: a resumed run is one run as far as the shortlist is
    concerned. `written_this_run` separates the two when a manifest is present.
    """
    results = load_stage(output_dir, PipelineStage.SCORE, ScoreResult)
    corpus_by_id = {record.readable_id: record for record in corpus}
    scored = [_as_scored(result) for result in results]
    scores = [document.score for document in scored if document.score is not None]
    usage_known = [
        result
        for result in results
        if result.input_tokens is not None and result.output_tokens is not None
    ]
    return RunSummary(
        generated_at=generated_at,
        output_dir=output_dir,
        manifest=manifest,
        corpus_size=len(corpus),
        with_text=sum(len(record.text.strip()) >= min_chars for record in corpus),
        results_total=len(results),
        written_this_run=(
            _written_since(output_dir, manifest.started_at) if manifest else None
        ),
        status_counts=dict(
            sorted(Counter(result.status.value for result in results).items())
        ),
        distribution=distribution(scored),
        mean_score=statistics.fmean(scores) if scores else None,
        median_score=statistics.median(scores) if scores else None,
        in_scope=sum(score >= IN_SCOPE_THRESHOLD for score in scores),
        shortlist=_shortlist(results, corpus_by_id),
        title_checks=dict(
            sorted(
                Counter(
                    document.title_check or "(absent)" for document in scored
                ).items()
            )
        ),
        truncated=sum(result.truncated for result in results),
        chars_sent=sum(result.chars_sent for result in results),
        original_chars=sum(result.original_chars for result in results),
        input_tokens=sum(result.input_tokens or 0 for result in usage_known),
        output_tokens=sum(result.output_tokens or 0 for result in usage_known),
        results_without_usage=len(results) - len(usage_known),
        corrupt=corrupt_extractions(scored, corpus, CID_ARTEFACT_THRESHOLD),
        invariance=invariance_groups(scored, corpus),
    )


def _percent(part: int, whole: int) -> str:
    return f"{part / whole:.1%}" if whole else "n/a"


def _stamp(moment: datetime) -> str:
    return moment.astimezone(UTC).strftime("%Y-%m-%d %H:%M:%SZ")


def _render_run(summary: RunSummary) -> list[str]:
    lines = ["## Run", ""]
    manifest = summary.manifest
    if manifest is None:
        lines.append(
            "No run manifest was found, so the configuration that produced these"
            + " results is not recorded here. Check `log.txt` in the output directory."
        )
        return lines
    configuration = manifest.configuration
    rows = [
        ("Started", _stamp(manifest.started_at)),
        ("Report generated", _stamp(summary.generated_at)),
        ("Model", configuration["model"]),
        ("Temperature", configuration["temperature"]),
        ("Rubric", configuration["rubric_path"]),
        ("Corpus", configuration["corpus_path"]),
        (
            "Text budget",
            f"{configuration['max_chars']} chars per document,"
            + f" head fraction {configuration['head_fraction']}",
        ),
        ("Documents selected", str(manifest.selected)),
        ("Forced rescoring", configuration["force"]),
    ]
    lines.append("| | |")
    lines.append("|---|---|")
    lines.extend(f"| {label} | {value} |" for label, value in rows)
    return lines


def _render_coverage(summary: RunSummary) -> list[str]:
    lines = [
        "## Coverage",
        "",
        f"- Corpus: {summary.corpus_size:,} records, of which"
        + f" {summary.with_text:,} carry enough extracted text to score"
        + f" ({_percent(summary.with_text, summary.corpus_size)}). The rest were not"
        + " sent to the model.",
        f"- Results on disk: {summary.results_total:,}"
        + f" ({_percent(summary.results_total, summary.with_text)} of the text-bearing"
        + " corpus).",
    ]
    if summary.written_this_run is not None:
        carried = summary.results_total - summary.written_this_run
        lines.append(
            f"- Written in this run: {summary.written_this_run:,}; carried over from"
            + f" earlier runs of this output directory: {carried:,}."
        )
    for status, count in summary.status_counts.items():
        lines.append(f"- Status `{status}`: {count:,}")
    failed = summary.results_total - summary.status_counts.get(
        ScoreStatus.SUCCESS.value, 0
    )
    if failed:
        lines.append(
            f"- {failed:,} document(s) have no score. Re-run to retry them; they are"
            + " counted above but excluded from every figure below."
        )
    return lines


def _render_scores(summary: RunSummary) -> list[str]:
    scored = sum(summary.distribution.values())
    lines = ["## Scores", ""]
    if not scored:
        lines.append("No documents were scored.")
        return lines
    lines.append("| Band | Documents | |")
    lines.append("|---|---:|---|")
    for label, count in summary.distribution.items():
        bar = "#" * round(40 * count / scored)
        lines.append(f"| {label.strip()} | {count:,} | `{bar}` |")
    lines.append("")
    lines.append(f"- Mean {summary.mean_score:.1f}, median {summary.median_score:.1f}.")
    lines.append(
        f"- At or above the in-scope threshold of {IN_SCOPE_THRESHOLD}:"
        + f" {summary.in_scope:,} of {scored:,} ({_percent(summary.in_scope, scored)})."
        + " This is the recall-first shortlist for analyst review."
    )
    lines.append(
        "- A single score carries a few points of run-to-run noise; membership at"
        + " the boundary will churn between runs."
    )
    return lines


def _render_shortlist(summary: RunSummary) -> list[str]:
    lines = [f"## Highest-scoring documents (top {SHORTLIST_SIZE})", ""]
    if not summary.shortlist:
        lines.append("None.")
        return lines
    lines.append("| Score | ID | Jurisdiction | Title (English) |")
    lines.append("|---:|---|---|---|")
    for entry in summary.shortlist:
        title = entry.name_english.replace("|", "\\|")
        lines.append(
            f"| {entry.score} | {entry.readable_id} | {entry.jurisdiction} | {title} |"
        )
    return lines


def _render_checks(summary: RunSummary) -> list[str]:
    lines = ["## Checks that need no ground truth", ""]

    lines.append("### Title verification")
    lines.append("")
    lines.append(
        "Whether the title the model returned actually occurs in the text it was"
        + " sent. `no` means treat the title as fabricated."
    )
    lines.append("")
    for value, count in summary.title_checks.items():
        lines.append(f"- `{value}`: {count:,}")
    lines.append("")

    lines.append("### Text handling")
    lines.append("")
    lines.append(
        f"- Truncated to fit the prompt: {summary.truncated:,} of"
        + f" {summary.results_total:,} documents"
        + f" ({_percent(summary.truncated, summary.results_total)})."
    )
    lines.append(
        f"- Characters sent: {summary.chars_sent:,} of {summary.original_chars:,}"
        + f" available ({_percent(summary.chars_sent, summary.original_chars)})."
    )
    lines.append("")

    lines.append("### Extraction quality")
    lines.append("")
    if summary.corrupt:
        lines.append(
            f"{len(summary.corrupt):,} scored document(s) are at least"
            + f" {CID_ARTEFACT_THRESHOLD:.0%} `(cid:NNN)` glyph codes. A score on text"
            + " this damaged is not supported by the text."
        )
        lines.append("")
        for readable_id, ratio, score in summary.corrupt[:EXAMPLES]:
            lines.append(f"- {readable_id}: {ratio:.0%} glyph codes, scored {score}")
    else:
        lines.append("No scored document exceeded the glyph-artefact threshold.")
    lines.append("")

    lines.append("### Text invariance")
    lines.append("")
    disagreeing = [group for group in summary.invariance if group.spread > 0]
    if not summary.invariance:
        lines.append("No two scored documents share byte-identical text.")
    else:
        lines.append(
            f"{len(summary.invariance):,} group(s) of documents share byte-identical"
            + f" text; {len(summary.invariance) - len(disagreeing):,} scored"
            + f" identically and {len(disagreeing):,} did not."
        )
        if disagreeing:
            lines.append(
                f"Worst spread: {disagreeing[0].spread} points. Identical text"
                + " cannot justify different scores; the metadata block can."
            )
            lines.append("")
            for group in disagreeing[:EXAMPLES]:
                pairs = ", ".join(
                    f"{readable_id}={score}"
                    for readable_id, score in zip(
                        group.readable_ids, group.scores, strict=True
                    )
                )
                lines.append(f"- spread {group.spread}: {pairs}")
    return lines


def _render_usage(summary: RunSummary) -> list[str]:
    lines = [
        "## Token usage",
        "",
        f"- Input tokens: {summary.input_tokens:,}",
        f"- Output tokens: {summary.output_tokens:,}",
    ]
    if summary.results_without_usage:
        lines.append(
            f"- {summary.results_without_usage:,} result(s) carry no usage figures"
            + " (failed calls, or a client that did not report them) and are not"
            + " counted above."
        )
    lines.append(
        "- Cost is not captured: the shared LLM client reports tokens only. Read"
        + " the spend from the provider's dashboard."
    )
    return lines


def _render_outputs(summary: RunSummary, export_csv: Path | None) -> list[str]:
    lines = [
        "## Outputs",
        "",
        f"- One JSON result per document under `{summary.output_dir / 'score'}`.",
    ]
    if export_csv is not None:
        lines.append(f"- Results CSV: `{export_csv}`.")
    lines.append(f"- Log: `{summary.output_dir / 'log.txt'}`.")
    lines.append(
        "- Deeper comparison against an earlier run:"
        + " `uv run -m agora_screening.compare --results <csv> --baseline <csv>`."
    )
    return lines


def render(summary: RunSummary, *, export_csv: Path | None) -> str:
    sections = [
        ["# AGORA screening run report"],
        _render_run(summary),
        _render_coverage(summary),
        _render_scores(summary),
        _render_shortlist(summary),
        _render_checks(summary),
        _render_usage(summary),
        _render_outputs(summary, export_csv),
    ]
    return "\n\n".join("\n".join(section) for section in sections) + "\n"


def write_report(
    *,
    output_dir: Path,
    corpus: Sequence[DocumentRecord],
    min_chars: int,
    manifest: RunManifest | None,
    report_path: Path,
    export_csv: Path | None,
) -> RunSummary:
    summary = summarise(
        output_dir=output_dir,
        corpus=corpus,
        min_chars=min_chars,
        manifest=manifest,
        generated_at=datetime.now(UTC),
    )
    report_path.parent.mkdir(parents=True, exist_ok=True)
    _ = report_path.write_text(render(summary, export_csv=export_csv), encoding="utf-8")
    logger.info(f"Wrote run report to {report_path}")
    return summary


class ReportSettings(
    BaseSettings,
    cli_parse_args=True,
    cli_enforce_required=True,
    cli_kebab_case=True,
    cli_implicit_flags=True,
    cli_hide_none_type=True,
    cli_prog_name="agora_screening.report",
):
    """
    Regenerate the run report for an existing output directory.

    The scoring run writes this report itself; use this to rebuild it after
    deleting or re-scoring individual results. Offline, no API calls.
    """

    output_dir: Path = Field(
        default=...,
        description="Pipeline output directory holding score results",
    )
    corpus_path: Path = Field(
        default=DEFAULT_CORPUS_PATH,
        description="Corpus CSV the results were scored from",
    )
    report_path: Path | None = Field(
        default=None,
        description="Where to write the report. Default: report.md in the output directory.",
    )
    export_csv: Path | None = Field(
        default=None,
        description="Results CSV to reference in the report, if one was exported",
    )
    min_chars: int = Field(
        default=200,
        description="Text threshold used by the run, for the coverage figures",
    )


def main() -> None:
    settings = ReportSettings()
    logging.basicConfig(level=logging.INFO)
    _ = write_report(
        output_dir=settings.output_dir,
        corpus=load_oecd_corpus(settings.corpus_path),
        min_chars=settings.min_chars,
        manifest=load_manifest(settings.output_dir),
        report_path=settings.report_path or settings.output_dir / REPORT_FILENAME,
        export_csv=settings.export_csv,
    )


if __name__ == "__main__":
    main()
