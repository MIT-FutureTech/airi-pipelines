from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings

from risk_repository.settings import (
    DEFAULT_AIRTABLE_BASE_ID,
    DEFAULT_AIRTABLE_TIMEOUT,
    DEFAULT_CONCURRENCY,
    DEFAULT_LLM_RATE_LIMIT_RPS,
    DEFAULT_MODEL,
)


class EvaluationSettings(
    BaseSettings,
    cli_parse_args=True,
    cli_enforce_required=True,
    cli_kebab_case=True,
    cli_implicit_flags=True,
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
    airtable_screening_table: str = Field(
        default=...,
        description="""
            Airtable screening table whose human review columns provide the screening
            ground truth.
        """,
    )
