from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings

from risk_repository.results import STAGE_ORDER, PipelineStage

DEFAULT_OUTPUT_DIR = Path(__file__).parent.parent.parent / "output"


class RiskRepositorySettings(
    BaseSettings,
    cli_parse_args=True,
    cli_enforce_required=True,
    cli_kebab_case=True,
    cli_implicit_flags=True,
    cli_hide_none_type=True,
    cli_prog_name="risk_repository",
):
    output_dir: Path = Field(
        default=DEFAULT_OUTPUT_DIR,
        description="Directory for pipeline output",
    )
    model: str = Field(
        default="gpt-5-mini-2025-08-07",
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
        default=5,
        description="Maximum number of concurrent tasks",
    )
    llm_rate_limit_rps: float = Field(
        default=10.0,
        description="LLM API rate limit in requests per second",
    )
    llm_timeout: float = Field(
        default=180.0,
        description="LLM API timeout in seconds",
    )
    airtable_timeout: float = Field(
        default=30.0,
        description="Airtable API timeout in seconds",
    )
    airtable_base_id: str = Field(
        default="app32FOUBa5WcUfEO",
        description="Airtable ID for the AI Risk Repository base",
    )
    airtable_table_name: str = Field(
        default="Documents",
        description="Airtable table name to fetch documents from",
    )
