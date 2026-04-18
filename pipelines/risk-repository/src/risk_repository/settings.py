from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings

from risk_repository.results import STAGE_ORDER, PipelineStage

DEFAULT_OUTPUT_DIR = Path(__file__).parent.parent.parent / "output"
DEFAULT_MODEL = "gpt-5-mini-2025-08-07"
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
    """Screen, extract, and classify AI risks from academic literature.

    Part of the AI Risk Repository project (https://airisk.mit.edu/).
    Documents are fetched from Airtable and processed through a multi-stage
    LLM pipeline. Results are saved to the output directory as JSON files.
    """

    output_dir: Path = Field(
        default=DEFAULT_OUTPUT_DIR,
        description="Directory for pipeline output",
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
        description="Specific document IDs to process",
    )
    stages: list[PipelineStage] = Field(
        default=STAGE_ORDER,
        description="Pipeline stages to run",
    )
    force: bool = Field(
        default=False,
        description="Reprocess documents even if results already exist",
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
    airtable_table_name: str = Field(
        default="Documents",
        description="Airtable table name to fetch documents from",
    )


class EvaluationSettings(
    BaseSettings,
    cli_parse_args=True,
    cli_enforce_required=True,
    cli_kebab_case=True,
    cli_hide_none_type=True,
    cli_prog_name="risk_repository.evaluate",
):
    """Evaluate pipeline results against ground truth from Airtable.

    Compares screening, extraction, and classification outputs to manually
    curated data, reporting multiple metrics include precision and recall.
    """

    results_dir: Path = Field(
        default=DEFAULT_OUTPUT_DIR,
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
        description="Maximum LLM attempts for risk matching before accepting partial results",
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
