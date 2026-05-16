from pathlib import Path
from typing import Self

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings

from risk_repository.records import TestTrainSplit
from risk_repository.results import STAGE_ORDER, PipelineStage

DEFAULT_DOWNLOAD_CACHE_DIR = Path(__file__).parent.parent.parent / "download_cache"
DEFAULT_MODEL = "openai/gpt-5-mini"
DEFAULT_CONCURRENCY = 5
DEFAULT_LLM_RATE_LIMIT_RPS = 10.0
DEFAULT_AIRTABLE_TIMEOUT = 30.0
DEFAULT_AIRTABLE_BASE_ID = "app32FOUBa5WcUfEO"


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
    split: TestTrainSplit = Field(
        default=TestTrainSplit.TRAIN,
        description="Split to process",
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
    airtable_documents_table: str | None = Field(
        default=None,
        description="""
            Airtable table name to fetch documents from. Mutually exclusive with
            --csv-path.
        """,
    )
    csv_path: Path | None = Field(
        default=None,
        description="""
            Path to a CSV file of documents to process. Mutually exclusive with
            --airtable-documents-table.
        """,
    )

    @model_validator(mode="after")
    def _validate_input_source(self) -> Self:
        has_airtable = self.airtable_documents_table is not None
        has_csv = self.csv_path is not None
        if has_airtable == has_csv:
            raise ValueError(
                "Provide exactly one of --airtable-documents-table or --csv-path"
            )
        return self


class EvaluationSettings(
    BaseSettings,
    cli_parse_args=True,
    cli_enforce_required=True,
    cli_kebab_case=True,
    cli_hide_none_type=True,
    cli_prog_name="risk_repository.evaluate",
):
    """
    Evaluate pipeline results against ground truth from Airtable.

    Compares screening, extraction, and classification outputs to manually
    curated data, reporting multiple metrics include precision and recall.
    """

    results_dir: Path = Field(
        default=...,
        description="Directory containing pipeline results to evaluate",
    )
    model: str = Field(
        default=DEFAULT_MODEL,
        description="LLM model to use for risk matching",
    )
    concurrency: int = Field(
        default=DEFAULT_CONCURRENCY,
        description="Maximum number of concurrent matching tasks",
    )
    max_attempts: int = Field(
        default=3,
        description="""
            Maximum LLM attempts for risk matching before accepting partial results
        """,
    )
    llm_rate_limit_rps: float = Field(
        default=DEFAULT_LLM_RATE_LIMIT_RPS,
        description="LLM API rate limit in requests per second",
    )
    llm_timeout: float = Field(
        default=120.0,
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
    airtable_documents_table: str = Field(
        default="Documents: Training Set",
        description="Airtable table name to fetch documents from",
    )
