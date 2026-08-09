from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings

from risk_repository.classify_pending.reviews import PIPELINE_REVIEWER_PREFIX
from risk_repository.settings import (
    DEFAULT_AIRTABLE_BASE_ID,
    DEFAULT_AIRTABLE_TIMEOUT,
    DEFAULT_CONCURRENCY,
    DEFAULT_LLM_RATE_LIMIT_RPS,
    DEFAULT_MODEL,
)

DEFAULT_RISKS_TABLE = "Risks 2026"
DEFAULT_REVIEWS_TABLE = "Classification Reviews 2026"
DEFAULT_LLM_TIMEOUT = 120.0


class ClassifyPendingSettings(
    BaseSettings,
    cli_parse_args=True,
    cli_enforce_required=True,
    cli_kebab_case=True,
    cli_implicit_flags=True,
    cli_hide_none_type=True,
    cli_prog_name="classify_pending",
):
    """Classify approved risks that the pipeline has not classified yet."""

    airtable_base_id: str = Field(
        default=DEFAULT_AIRTABLE_BASE_ID,
        description="Airtable base holding the risks and reviews tables",
    )
    risks_table: str = Field(
        default=DEFAULT_RISKS_TABLE,
        description="Table holding approved risks",
    )
    reviews_table: str = Field(
        default=DEFAULT_REVIEWS_TABLE,
        description="Table holding classification review rows",
    )
    quick_ref: list[str] = Field(
        default=[],
        description="""
            Restrict to the specified papers.
            Default: every paper with pending risks.
        """,
    )
    pipeline_reviewer: str = Field(
        default=...,
        description="""
            Reviewer name to attribute the pipeline's rows to. Must start with
            'pipeline:' so the review app can tell it apart from a human.
        """,
    )

    @field_validator("pipeline_reviewer")
    @classmethod
    def _distinguishable_from_a_human(cls, value: str) -> str:
        if not value.startswith(PIPELINE_REVIEWER_PREFIX):
            raise ValueError(f"must start with {PIPELINE_REVIEWER_PREFIX!r}")
        return value

    model: str = Field(
        default=DEFAULT_MODEL,
        description="LLM model to classify with",
    )
    concurrency: int = Field(
        default=DEFAULT_CONCURRENCY,
        description="Number of risks to classify at once",
    )
    llm_rate_limit_rps: float = Field(
        default=DEFAULT_LLM_RATE_LIMIT_RPS,
        description="Maximum LLM requests per second",
    )
    llm_timeout: float = Field(
        default=DEFAULT_LLM_TIMEOUT,
        description="Timeout in seconds for a single LLM request",
    )
    airtable_timeout: float = Field(
        default=DEFAULT_AIRTABLE_TIMEOUT,
        description="Timeout in seconds for a single Airtable request",
    )
    force: bool = Field(
        default=False,
        description="Reclassify risks that already have a pipeline classification",
    )
    dry_run: bool = Field(
        default=False,
        description="Report what would be classified without calling the LLM",
    )
    log_path: Path | None = Field(
        default=None,
        description="Append log output to the given path",
    )
