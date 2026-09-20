import csv
import hashlib
from collections import defaultdict
from collections.abc import Sequence
from pathlib import Path

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings

from agora_screening.corpus import DocumentRecord, load_oecd_corpus
from agora_screening.documents import cid_artefact_ratio
from agora_screening.settings import DEFAULT_CORPUS_PATH

IN_SCOPE_THRESHOLD = 60
BAND_WIDTH = 10
CID_ARTEFACT_THRESHOLD = 0.1
_CSV_FIELD_SIZE_LIMIT = 2**31 - 1


class ScoredDocument(BaseModel, frozen=True):
    readable_id: str
    score: int | None
    title_check: str


class InvarianceGroup(BaseModel, frozen=True):
    """Documents whose source text is byte-identical but whose scores are not.

    The text is the only evidence the rubric admits, so a spread here is the
    metadata block influencing the score despite the prompt forbidding it.
    """

    readable_ids: list[str]
    scores: list[int]

    @property
    def spread(self) -> int:
        return max(self.scores) - min(self.scores)


def read_results(csv_path: Path) -> list[ScoredDocument]:
    """Read a results CSV, ours or the proof of concept's.

    Both carry `ID`, `Scope score` and the title-check column, which is all the
    comparison needs.
    """
    documents: list[ScoredDocument] = []
    previous_limit = csv.field_size_limit(_CSV_FIELD_SIZE_LIMIT)
    try:
        with csv_path.open(encoding="utf-8-sig", newline="") as handle:
            for row in csv.DictReader(handle):
                raw_score = (row.get("Scope score") or "").strip()
                documents.append(
                    ScoredDocument(
                        readable_id=row["ID"],
                        score=int(raw_score) if raw_score else None,
                        title_check=(
                            row.get("Name (original language) found in text") or ""
                        ),
                    )
                )
    finally:
        csv.field_size_limit(previous_limit)
    return documents


def band(score: int) -> str:
    low = min(score // BAND_WIDTH * BAND_WIDTH, 90)
    return f"{low:>3}-{low + BAND_WIDTH - 1:<3}"


def distribution(documents: Sequence[ScoredDocument]) -> dict[str, int]:
    counts: dict[str, int] = defaultdict(int)
    for document in documents:
        if document.score is not None:
            counts[band(document.score)] += 1
    return dict(sorted(counts.items()))


def invariance_groups(
    documents: Sequence[ScoredDocument],
    corpus: Sequence[DocumentRecord],
) -> list[InvarianceGroup]:
    """Group scored documents by the hash of their source text."""
    scores = {
        document.readable_id: document.score
        for document in documents
        if document.score is not None
    }
    by_text: dict[str, list[str]] = defaultdict(list)
    for record in corpus:
        if record.readable_id in scores:
            digest = hashlib.sha256(record.text.encode("utf-8")).hexdigest()
            by_text[digest].append(record.readable_id)
    groups = [
        InvarianceGroup(
            readable_ids=readable_ids,
            scores=[scores[readable_id] for readable_id in readable_ids],
        )
        for readable_ids in by_text.values()
        if len(readable_ids) > 1
    ]
    return sorted(groups, key=lambda group: group.spread, reverse=True)


def corrupt_extractions(
    documents: Sequence[ScoredDocument],
    corpus: Sequence[DocumentRecord],
    threshold: float,
) -> list[tuple[str, float, int]]:
    """Scored documents whose text is substantially `(cid:NNN)` glyph codes."""
    scores = {
        document.readable_id: document.score
        for document in documents
        if document.score is not None
    }
    found: list[tuple[str, float, int]] = []
    for record in corpus:
        score = scores.get(record.readable_id)
        if score is None:
            continue
        ratio = cid_artefact_ratio(record.text)
        if ratio >= threshold:
            found.append((record.readable_id, ratio, score))
    return sorted(found, key=lambda row: row[1], reverse=True)


class ScoreDelta(BaseModel, frozen=True):
    readable_id: str
    baseline: int
    current: int

    @property
    def delta(self) -> int:
        return self.current - self.baseline

    @property
    def crosses_threshold(self) -> bool:
        return (self.baseline >= IN_SCOPE_THRESHOLD) != (
            self.current >= IN_SCOPE_THRESHOLD
        )


def score_deltas(
    current: Sequence[ScoredDocument],
    baseline: Sequence[ScoredDocument],
) -> list[ScoreDelta]:
    baseline_scores = {
        document.readable_id: document.score
        for document in baseline
        if document.score is not None
    }
    deltas: list[ScoreDelta] = []
    for document in current:
        previous = baseline_scores.get(document.readable_id)
        if previous is None or document.score is None:
            continue
        deltas.append(
            ScoreDelta(
                readable_id=document.readable_id,
                baseline=previous,
                current=document.score,
            )
        )
    return sorted(deltas, key=lambda row: abs(row.delta), reverse=True)


class CompareSettings(
    BaseSettings,
    cli_parse_args=True,
    cli_enforce_required=True,
    cli_kebab_case=True,
    cli_implicit_flags=True,
    cli_hide_none_type=True,
    cli_prog_name="agora_screening.compare",
):
    """
    Report on a scoring run: score distribution, invariance and extraction quality.

    With a baseline, also reports per-document score movement. Runs entirely
    offline against CSV exports; it makes no API calls.
    """

    results: Path = Field(
        default=...,
        description="Results CSV to report on",
    )
    baseline: Path | None = Field(
        default=None,
        description="Earlier results CSV to compare against, keyed by document ID",
    )
    corpus_path: Path = Field(
        default=DEFAULT_CORPUS_PATH,
        description="Corpus CSV, needed for the text-invariance and extraction checks",
    )
    cid_artefact_threshold: float = Field(
        default=CID_ARTEFACT_THRESHOLD,
        description="Flag scored documents whose text is at least this fraction glyph codes",
    )
    examples: int = Field(
        default=5,
        description="Number of worst offenders to print per section",
    )


def _print_distribution(documents: Sequence[ScoredDocument]) -> None:
    scored = [document for document in documents if document.score is not None]
    print(f"\n## Score distribution ({len(scored)} scored, {len(documents)} rows)")
    if not scored:
        return
    scores = [document.score for document in scored if document.score is not None]
    for label, count in distribution(documents).items():
        bar = "#" * round(40 * count / len(scored))
        print(f"  {label} {count:>5}  {bar}")
    in_scope = sum(score >= IN_SCOPE_THRESHOLD for score in scores)
    print(f"  mean {sum(scores) / len(scores):.1f}")
    print(
        f"  at or above {IN_SCOPE_THRESHOLD}: {in_scope} ({in_scope / len(scores):.1%})"
    )


def _print_title_checks(documents: Sequence[ScoredDocument]) -> None:
    counts: dict[str, int] = defaultdict(int)
    for document in documents:
        counts[document.title_check or "(absent)"] += 1
    print("\n## Title verification")
    for value, count in sorted(counts.items()):
        flag = "  <-- treat as fabricated" if value == "no" and count else ""
        print(f"  {value:>10}: {count}{flag}")


def _print_invariance(groups: Sequence[InvarianceGroup], examples: int) -> None:
    disagreeing = [group for group in groups if group.spread > 0]
    print(f"\n## Text invariance ({len(groups)} groups share text byte-identically)")
    if not groups:
        return
    print(f"  groups scoring identically: {len(groups) - len(disagreeing)}")
    print(f"  groups disagreeing:         {len(disagreeing)}")
    if not disagreeing:
        print("  PASS: identical text always produced identical scores")
        return
    print(f"  worst spread:               {disagreeing[0].spread} points")
    print("  Identical text cannot justify different scores; the metadata block can.")
    for group in disagreeing[:examples]:
        pairs = ", ".join(
            f"{readable_id}={score}"
            for readable_id, score in zip(group.readable_ids, group.scores, strict=True)
        )
        print(f"    spread {group.spread:>3}: {pairs}")


def _print_corrupt_extractions(
    rows: Sequence[tuple[str, float, int]], examples: int
) -> None:
    print(
        f"\n## Extraction quality ({len(rows)} scored documents above the artefact threshold)"
    )
    for readable_id, ratio, score in rows[:examples]:
        print(f"    {readable_id}: {ratio:.0%} glyph codes, scored {score}")
    if rows:
        print("  A score on text this damaged is not supported by the text.")


def _print_deltas(deltas: Sequence[ScoreDelta], examples: int) -> None:
    print(f"\n## Movement against baseline ({len(deltas)} documents in both)")
    if not deltas:
        return
    absolute = [abs(delta.delta) for delta in deltas]
    unchanged = sum(value == 0 for value in absolute)
    crossings = [delta for delta in deltas if delta.crosses_threshold]
    print(f"  unchanged:        {unchanged} ({unchanged / len(deltas):.1%})")
    print(f"  mean |delta|:     {sum(absolute) / len(absolute):.2f}")
    print(f"  max |delta|:      {max(absolute)}")
    print(f"  crossing {IN_SCOPE_THRESHOLD}:      {len(crossings)}")
    for delta in deltas[:examples]:
        print(
            f"    {delta.readable_id}: {delta.baseline} -> {delta.current} ({delta.delta:+d})"
        )


def main() -> None:
    settings = CompareSettings()
    documents = read_results(settings.results)
    corpus = load_oecd_corpus(settings.corpus_path)

    print(f"# {settings.results.name}")
    _print_distribution(documents)
    _print_title_checks(documents)
    _print_invariance(invariance_groups(documents, corpus), settings.examples)
    _print_corrupt_extractions(
        corrupt_extractions(documents, corpus, settings.cid_artefact_threshold),
        settings.examples,
    )
    if settings.baseline is not None:
        _print_deltas(
            score_deltas(documents, read_results(settings.baseline)), settings.examples
        )


if __name__ == "__main__":
    main()
