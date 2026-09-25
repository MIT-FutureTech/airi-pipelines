import csv
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from agora_screening.corpus import DocumentRecord, load_oecd_corpus
from agora_screening.report import (
    REPORT_FILENAME,
    RunManifest,
    load_manifest,
    render,
    summarise,
    write_manifest,
    write_report,
)
from agora_screening.results import PipelineStage, result_path, save
from agora_screening.score import ScopeAssessment, ScoreResult, ScoreStatus
from agora_screening.settings import AgoraScreeningSettings
from agora_screening.titles import TitleCheck

_CORPUS_COLUMNS = [
    "Aggregator Link",
    "Aggregator Summary",
    "Link",
    "Name",
    "Jurisdiction",
    "Organization",
    "Date introduced",
    "Most recent activity",
    "Most recent activity date",
    "Category",
    "Initiative type",
    "Binding",
    "ID",
    "Text",
]

_TEXT = "Article 1. Providers of AI systems shall register. " * 10


def _row(readable_id: str, text: str, jurisdiction: str) -> dict[str, str]:
    return dict.fromkeys(_CORPUS_COLUMNS, "") | {
        "ID": readable_id,
        "Text": text,
        "Name": f"Initiative {readable_id}",
        "Jurisdiction": jurisdiction,
        "Aggregator Link": f"https://oecd.ai/en/dashboards/policy-initiatives/{readable_id}",
    }


@pytest.fixture
def corpus_path(tmp_path: Path) -> Path:
    path = tmp_path / "corpus.csv"
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=_CORPUS_COLUMNS)
        writer.writeheader()
        writer.writerow(_row("ID_0001", _TEXT, "Testland"))
        writer.writerow(_row("ID_0002", _TEXT, "Otherland"))
        writer.writerow(_row("ID_0003", "(cid:3)(cid:4)(cid:5)" * 20, "Glyphia"))
        writer.writerow(_row("ID_0004", "", "Textless"))
    return path


@pytest.fixture
def corpus(corpus_path: Path) -> list[DocumentRecord]:
    return load_oecd_corpus(corpus_path)


def _result(
    readable_id: str,
    score: int | None,
    *,
    truncated: bool = False,
) -> ScoreResult:
    if score is None:
        return ScoreResult(
            readable_id=readable_id,
            slug=readable_id,
            status=ScoreStatus.UNPARSEABLE_MODEL_OUTPUT,
            assessment=None,
            title_check=None,
            model=None,
            input_tokens=None,
            output_tokens=None,
            chars_sent=100,
            original_chars=100,
            truncated=False,
            cid_artefact_ratio=0.0,
        )
    return ScoreResult(
        readable_id=readable_id,
        slug=readable_id,
        status=ScoreStatus.SUCCESS,
        assessment=ScopeAssessment(
            name_original_language="Title",
            name_original_language_code="en",
            name_english=f"Title of {readable_id}",
            scope_score=score,
            scope_score_rationale="Because.",
        ),
        title_check=TitleCheck.YES,
        model="stub/model",
        input_tokens=100,
        output_tokens=10,
        chars_sent=500 if truncated else 100,
        original_chars=1_000 if truncated else 100,
        truncated=truncated,
        cid_artefact_ratio=0.0,
    )


@pytest.fixture
def output_dir(tmp_path: Path) -> Path:
    directory = tmp_path / "output"
    for result in [
        _result("ID_0001", 85, truncated=True),
        _result("ID_0002", 20),
        _result("ID_0003", 75),
        _result("ID_0004", None),
    ]:
        save(result_path(directory, PipelineStage.SCORE, result.readable_id), result)
    return directory


@pytest.fixture
def manifest() -> RunManifest:
    return RunManifest(
        started_at=datetime.now(UTC) - timedelta(minutes=1),
        selected=4,
        configuration={
            "model": "stub/model",
            "temperature": "0.0",
            "rubric_path": "prompts/agora_scope.md",
            "corpus_path": "corpus.csv",
            "max_chars": "40000",
            "head_fraction": "0.75",
            "force": "False",
        },
    )


class TestSummarise:
    def test_counts_cover_every_result_on_disk(
        self, output_dir: Path, corpus: list[DocumentRecord], manifest: RunManifest
    ) -> None:
        summary = summarise(
            output_dir=output_dir,
            corpus=corpus,
            min_chars=200,
            manifest=manifest,
            generated_at=datetime.now(UTC),
        )

        assert summary.corpus_size == 4
        assert summary.with_text == 3
        assert summary.results_total == 4
        assert summary.written_this_run == 4
        assert summary.status_counts == {
            "success": 3,
            "failed: unparseable model output": 1,
        }

    def test_scores_exclude_failed_results(
        self, output_dir: Path, corpus: list[DocumentRecord], manifest: RunManifest
    ) -> None:
        summary = summarise(
            output_dir=output_dir,
            corpus=corpus,
            min_chars=200,
            manifest=manifest,
            generated_at=datetime.now(UTC),
        )

        assert summary.distribution == {" 20-29 ": 1, " 70-79 ": 1, " 80-89 ": 1}
        assert summary.mean_score == 60
        assert summary.median_score == 75
        assert summary.in_scope == 2
        assert [entry.readable_id for entry in summary.shortlist] == [
            "ID_0001",
            "ID_0003",
            "ID_0002",
        ]
        assert summary.shortlist[0].jurisdiction == "Testland"

    def test_checks_and_usage_are_totalled(
        self, output_dir: Path, corpus: list[DocumentRecord], manifest: RunManifest
    ) -> None:
        summary = summarise(
            output_dir=output_dir,
            corpus=corpus,
            min_chars=200,
            manifest=manifest,
            generated_at=datetime.now(UTC),
        )

        assert summary.title_checks == {"(absent)": 1, "yes": 3}
        assert summary.truncated == 1
        assert summary.input_tokens == 300
        assert summary.output_tokens == 30
        assert summary.results_without_usage == 1
        assert [readable_id for readable_id, _, _ in summary.corrupt] == ["ID_0003"]
        assert len(summary.invariance) == 1
        assert summary.invariance[0].spread == 65

    def test_results_written_before_the_run_are_carried_over(
        self, output_dir: Path, corpus: list[DocumentRecord], manifest: RunManifest
    ) -> None:
        later = manifest.model_copy(
            update={"started_at": datetime.now(UTC) + timedelta(hours=1)}
        )

        summary = summarise(
            output_dir=output_dir,
            corpus=corpus,
            min_chars=200,
            manifest=later,
            generated_at=datetime.now(UTC),
        )

        assert summary.written_this_run == 0

    def test_an_empty_output_directory_is_reported_not_crashed(
        self, tmp_path: Path, corpus: list[DocumentRecord]
    ) -> None:
        summary = summarise(
            output_dir=tmp_path / "empty",
            corpus=corpus,
            min_chars=200,
            manifest=None,
            generated_at=datetime.now(UTC),
        )

        assert summary.results_total == 0
        assert summary.mean_score is None
        assert summary.written_this_run is None
        assert "No documents were scored." in render(summary, export_csv=None)


class TestRender:
    def test_every_section_is_present(
        self, output_dir: Path, corpus: list[DocumentRecord], manifest: RunManifest
    ) -> None:
        summary = summarise(
            output_dir=output_dir,
            corpus=corpus,
            min_chars=200,
            manifest=manifest,
            generated_at=datetime.now(UTC),
        )

        text = render(summary, export_csv=Path("results.csv"))

        for heading in [
            "## Run",
            "## Coverage",
            "## Scores",
            "## Highest-scoring documents",
            "### Title verification",
            "### Text handling",
            "### Extraction quality",
            "### Text invariance",
            "## Token usage",
            "## Outputs",
        ]:
            assert heading in text
        assert "| Model | stub/model |" in text
        assert "At or above the in-scope threshold of 60: 2 of 3 (66.7%)" in text
        assert "| 85 | ID_0001 | Testland | Title of ID_0001 |" in text
        assert "ID_0003: 100% glyph codes, scored 75" in text
        assert "spread 65: ID_0001=85, ID_0002=20" in text
        assert "Results CSV: `results.csv`" in text

    def test_a_missing_manifest_is_said_so(
        self, output_dir: Path, corpus: list[DocumentRecord]
    ) -> None:
        summary = summarise(
            output_dir=output_dir,
            corpus=corpus,
            min_chars=200,
            manifest=None,
            generated_at=datetime.now(UTC),
        )

        assert "No run manifest was found" in render(summary, export_csv=None)


class TestFiles:
    def test_manifest_round_trips_through_the_output_directory(
        self, tmp_path: Path, corpus_path: Path
    ) -> None:
        settings = AgoraScreeningSettings(
            _cli_parse_args=False,  # pyright: ignore[reportCallIssue]
            output_dir=tmp_path / "output",
            corpus_path=corpus_path,
        )
        started_at = datetime.now(UTC)

        written = write_manifest(settings, selected=3, started_at=started_at)
        loaded = load_manifest(settings.output_dir)

        assert loaded == written
        assert loaded is not None
        assert loaded.configuration["model"] == settings.model
        assert loaded.configuration["corpus_path"] == str(corpus_path)

    def test_no_manifest_loads_as_none(self, tmp_path: Path) -> None:
        assert load_manifest(tmp_path) is None

    def test_write_report_lands_in_the_output_directory(
        self, output_dir: Path, corpus: list[DocumentRecord], manifest: RunManifest
    ) -> None:
        report_path = output_dir / REPORT_FILENAME

        summary = write_report(
            output_dir=output_dir,
            corpus=corpus,
            min_chars=200,
            manifest=manifest,
            report_path=report_path,
            export_csv=None,
        )

        assert summary.results_total == 4
        assert report_path.read_text(encoding="utf-8").startswith(
            "# AGORA screening run report"
        )
