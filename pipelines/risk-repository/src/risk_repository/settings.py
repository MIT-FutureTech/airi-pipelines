from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings

from risk_repository.records import DocumentSource
from risk_repository.results import STAGE_ORDER, PipelineStage

DEFAULT_DOWNLOAD_CACHE_DIR = Path(__file__).parent.parent.parent / "download_cache"
DEFAULT_MODEL = "google/gemini-3-flash-preview"
DEFAULT_CONCURRENCY = 5
DEFAULT_LLM_RATE_LIMIT_RPS = 10.0
DEFAULT_AIRTABLE_BASE_ID = "app32FOUBa5WcUfEO"
DEFAULT_AIRTABLE_TIMEOUT = 30.0


class RiskRepositorySettings(
    BaseSettings,
    cli_parse_args=True,
    cli_enforce_required=True,
    cli_kebab_case=True,
    cli_implicit_flags=True,
    cli_hide_none_type=True,
    cli_prog_name="risk_repository",
):
    """
    Screen, extract, and classify AI risks from academic literature.

    Part of the AI Risk Repository project (https://airisk.mit.edu/).
    Documents are fetched from Airtable and processed through a multi-stage
    LLM pipeline. Results are saved to the output directory as JSON files.
    """

    output_dir: Path = Field(
        default=...,
        description="Directory for pipeline output",
    )
    download_cache_dir: Path = Field(
        default=DEFAULT_DOWNLOAD_CACHE_DIR,
        description="""
            Directory for cached PDF downloads and per-document fetch failure records.
        """,
    )
    log_path: Path | None = Field(
        default=None,
        description="""
            Append log output to given path. Default: log.txt in the output directory.
        """,
    )
    model: str = Field(
        default=DEFAULT_MODEL,
        description="LLM model to use for all pipeline stages",
    )
    limit: int | None = Field(
        default=None,
        description="Maximum number of documents to process",
    )
    document_ids: list[str] | None = Field(
        default=None,
        description="Comma-separated list of document IDs to process",
    )
    stages: list[PipelineStage] = Field(
        default=STAGE_ORDER,
        description="Comma-separated list of pipeline stages to run",
    )
    force: bool = Field(
        default=False,
        description="Reprocess documents even if results already exist",
    )
    document_max_truncation_ratio: float = Field(
        default=0.55,
        description="""
            If truncating references and appendices from the end of the document would
            remove more than this fraction of the document's length, raise an error.
        """,
    )
    document_length_limit: int = Field(
        default=1_000_000,
        description="""
            After removing references nd appendices, truncate the document to not exceed
            this length in terms of number of characters.
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
    airtable_timeout: float = Field(
        default=DEFAULT_AIRTABLE_TIMEOUT,
        description="Airtable API timeout in seconds",
    )
    airtable_base_id: str = Field(
        default=DEFAULT_AIRTABLE_BASE_ID,
        description="Airtable ID for the AI Risk Repository base",
    )
    document_source: DocumentSource = Field(
        default=DocumentSource.SCREENING_TABLE,
        description="""
            How to interpret the source table: a screening table (PDF attachments, keyed
            by record ID) or the curated training-set table (full text by URL, keyed by
            QuickRef).
        """,
    )
    airtable_source_table: str = Field(
        default=...,
        description="""
            Airtable table to read documents from, interpreted according to
            document_source. For screening_table, each record's PDF is read from its
            full_text_pdf attachment and decisions are written back by
            `risk_repository.upload`. For training_set, full text is fetched from each
            record's PDFURL or URL.
        """,
    )
    airtable_view: str | None = Field(
        default=None,
        description="""
            Airtable view (name or ID) to read documents from. When set, only records
            in the view are processed, in the view's order and subject to its filters.
        """,
    )
