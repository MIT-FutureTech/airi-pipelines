import csv
from collections.abc import Sequence
from pathlib import Path
from types import TracebackType
from typing import Self

import pytest
from pydantic import BaseModel

from agora_screening.corpus import DocumentRecord, load_oecd_corpus, select_with_text
from agora_screening.export import export_csv
from agora_screening.results import PipelineStage, result_path
from agora_screening.score import ScopeAssessment, ScoreResult, ScoreStatus, run_scoring
from agora_screening.settings import AgoraScreeningSettings
from agora_screening.titles import TitleCheck
from toolbox.llm import Message, StructuredResult, TextResult, TokenUsage

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

_DOCUMENT_TEXT = "National AI Strategy\n\n" + ("Article 1. Providers shall. " * 40)


class StubLLMClient:
    """An LLM client that returns a fixed assessment and counts its calls."""

    _assessment: ScopeAssessment
    calls: int
    prompts: list[str]

    def __init__(self, assessment: ScopeAssessment) -> None:
        self._assessment = assessment
        self.calls = 0
        self.prompts = []

    async def generate(self, messages: Sequence[Message]) -> TextResult:
        _ = messages
        raise NotImplementedError

    async def generate_structured[T: BaseModel](
        self,
        messages: Sequence[Message],
        schema: type[T],
    ) -> StructuredResult[T]:
        self.calls += 1
        self.prompts.append(messages[-1].content)
        assert schema is ScopeAssessment
        return StructuredResult[T](
            value=self._assessment,  # pyright: ignore[reportArgumentType]
            model="stub/model",
            usage=TokenUsage(input_tokens=11, output_tokens=7),
        )

    async def close(self) -> None:
        return None

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        return None


@pytest.fixture
def corpus_path(tmp_path: Path) -> Path:
    path = tmp_path / "corpus.csv"
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=_CORPUS_COLUMNS)
        writer.writeheader()
        writer.writerow(
            {
                "ID": "ID_0001",
                "Text": _DOCUMENT_TEXT,
                "Name": "National AI Strategy",
                "Jurisdiction": "Testland",
                "Category": "Regulations, guidelines and standards",
                "Aggregator Link": "https://oecd.ai/en/dashboards/policy-initiatives/national-ai",
                "Link": "https://example.test/strategy.pdf",
            }
        )
        writer.writerow(dict.fromkeys(_CORPUS_COLUMNS, "") | {"ID": "ID_0002"})
    return path


@pytest.fixture
def records(corpus_path: Path) -> list[DocumentRecord]:
    return select_with_text(load_oecd_corpus(corpus_path), min_chars=200)


@pytest.fixture
def settings(tmp_path: Path, corpus_path: Path) -> AgoraScreeningSettings:
    # pydantic-settings accepts the underscore-prefixed init kwargs at runtime but
    # does not declare them, and without this one the settings object would parse
    # pytest's own argv.
    return AgoraScreeningSettings(
        _cli_parse_args=False,  # pyright: ignore[reportCallIssue]
        output_dir=tmp_path / "output",
        corpus_path=corpus_path,
    )


@pytest.fixture
def client() -> StubLLMClient:
    return StubLLMClient(
        ScopeAssessment(
            name_original_language="National AI Strategy",
            name_original_language_code="en",
            name_english="National AI Strategy",
            scope_score=85,
            scope_score_rationale="Operative provisions addressing AI directly.",
        )
    )


async def test_scoring_writes_one_result_per_document(
    records: list[DocumentRecord],
    settings: AgoraScreeningSettings,
    client: StubLLMClient,
) -> None:
    await run_scoring(records, llm=client, system_prompt="system", settings=settings)

    path = result_path(settings.output_dir, PipelineStage.SCORE, "ID_0001")
    result = ScoreResult.model_validate_json(path.read_text(encoding="utf-8"))
    assert result.status == ScoreStatus.SUCCESS
    assert result.assessment is not None
    assert result.assessment.scope_score == 85
    assert result.model == "stub/model"
    assert result.input_tokens == 11


async def test_textless_documents_are_never_sent(
    records: list[DocumentRecord],
    settings: AgoraScreeningSettings,
    client: StubLLMClient,
) -> None:
    await run_scoring(records, llm=client, system_prompt="system", settings=settings)

    assert client.calls == 1
    assert not result_path(settings.output_dir, PipelineStage.SCORE, "ID_0002").exists()


async def test_the_title_check_runs_against_what_was_sent(
    records: list[DocumentRecord],
    settings: AgoraScreeningSettings,
    client: StubLLMClient,
) -> None:
    await run_scoring(records, llm=client, system_prompt="system", settings=settings)

    path = result_path(settings.output_dir, PipelineStage.SCORE, "ID_0001")
    result = ScoreResult.model_validate_json(path.read_text(encoding="utf-8"))
    assert result.title_check == TitleCheck.YES


async def test_a_second_run_resumes_instead_of_rescoring(
    records: list[DocumentRecord],
    settings: AgoraScreeningSettings,
    client: StubLLMClient,
) -> None:
    await run_scoring(records, llm=client, system_prompt="system", settings=settings)
    await run_scoring(records, llm=client, system_prompt="system", settings=settings)

    assert client.calls == 1


async def test_force_rescores_an_existing_result(
    records: list[DocumentRecord],
    settings: AgoraScreeningSettings,
    client: StubLLMClient,
) -> None:
    await run_scoring(records, llm=client, system_prompt="system", settings=settings)
    await run_scoring(
        records,
        llm=client,
        system_prompt="system",
        settings=settings.model_copy(update={"force": True}),
    )

    assert client.calls == 2


async def test_metadata_reaches_the_prompt_as_context(
    records: list[DocumentRecord],
    settings: AgoraScreeningSettings,
    client: StubLLMClient,
) -> None:
    await run_scoring(records, llm=client, system_prompt="system", settings=settings)

    prompt = client.prompts[0]
    assert "Jurisdiction: Testland" in prompt
    assert "Article 1. Providers shall." in prompt


async def test_export_writes_a_row_per_scored_document(
    records: list[DocumentRecord],
    settings: AgoraScreeningSettings,
    client: StubLLMClient,
    tmp_path: Path,
) -> None:
    await run_scoring(records, llm=client, system_prompt="system", settings=settings)
    csv_path = tmp_path / "results.csv"

    assert export_csv(records, output_dir=settings.output_dir, csv_path=csv_path) == 1

    with csv_path.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == 1
    assert rows[0]["ID"] == "ID_0001"
    assert rows[0]["Scope score"] == "85"
    assert rows[0]["Name (original language) found in text"] == "yes"
    assert rows[0]["LLM query status"] == "success"
    assert rows[0]["truncated"] == "no"
