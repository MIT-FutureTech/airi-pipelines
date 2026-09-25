from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings

from agora_screening.prompts import DEFAULT_RUBRIC_PATH

_PIPELINE_DIR = Path(__file__).parent.parent.parent
DEFAULT_CORPUS_PATH = (
    _PIPELINE_DIR / "input" / "oecd_policy_initiatives_extracted_results.csv"
)
DEFAULT_MODEL = "google/gemini-3.5-flash-lite"
DEFAULT_CONCURRENCY = 5
DEFAULT_LLM_RATE_LIMIT_RPS = 10.0


class AgoraScreeningSettings(
    BaseSettings,
    cli_parse_args=True,
    cli_enforce_required=True,
    cli_kebab_case=True,
    cli_implicit_flags=True,
    cli_hide_none_type=True,
    cli_prog_name="agora_screening",
):
    """
    Score candidate policy documents for how well they fall within AGORA's scope.

    Documents are read from a corpus CSV carrying pre-extracted text. Each is
    scored 0-100 against the rubric in prompts/agora_scope.md, with one JSON
    result file per document so a run can be resumed or partially re-run.
    """

    output_dir: Path = Field(
        default=...,
        description="Directory for pipeline output",
    )
    corpus_path: Path = Field(
        default=DEFAULT_CORPUS_PATH,
        description="CSV of candidate documents with pre-extracted text",
    )
    rubric_path: Path = Field(
        default=DEFAULT_RUBRIC_PATH,
        description="""
            Markdown file holding AGORA's scoping definition and the banded rubric.
            Injected wholesale into the system prompt.
        """,
    )
    export_csv: Path | None = Field(
        default=None,
        description="""
            Also write results to this CSV after scoring. Without it, results remain
            as one JSON file per document under the output directory.
        """,
    )
    log_path: Path | None = Field(
        default=None,
        description="Append log output to given path. Default: log.txt in the output directory.",
    )
    report_path: Path | None = Field(
        default=None,
        description="""
            Write the end-of-run summary report to this path. Default: report.md in
            the output directory.
        """,
    )
    model: str = Field(
        default=DEFAULT_MODEL,
        description="LLM model to use for scoring",
    )
    temperature: float = Field(
        default=0.0,
        description="""
            Sampling temperature. Zero by default, but note that this does NOT make
            scoring deterministic: re-running 100 documents unchanged reproduced 72
            of them exactly, 91 within five points, and moved three by more than
            twenty. Treat a single document's score as carrying a few points of
            noise either way.
        """,
    )
    limit: int | None = Field(
        default=None,
        description="Maximum number of documents to process",
    )
    document_ids: list[str] | None = Field(
        default=None,
        description="Comma-separated list of document IDs to process",
    )
    force: bool = Field(
        default=False,
        description="Reprocess documents even if results already exist",
    )
    min_chars: int = Field(
        default=200,
        description="""
            Documents with less extracted text than this are treated as having none
            and are not scored. Excludes a handful of junk extractions.
        """,
    )
    max_chars: int = Field(
        default=40_000,
        description="Per-document character cap on the text sent to the model",
    )
    head_fraction: float = Field(
        default=0.75,
        description="""
            Share of the character budget given to the start of a truncated document.
            The remainder goes to its end; the middle is dropped.
        """,
    )
    concurrency: int = Field(
        default=DEFAULT_CONCURRENCY,
        description="Maximum number of concurrent tasks",
    )
    llm_rate_limit_rps: float = Field(
        default=DEFAULT_LLM_RATE_LIMIT_RPS,
        description="LLM API rate limit in requests per second",
    )
    llm_timeout: float = Field(
        default=180.0,
        description="LLM API timeout in seconds",
    )
