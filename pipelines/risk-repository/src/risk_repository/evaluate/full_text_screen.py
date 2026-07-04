import asyncio
import logging

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings

from risk_repository.evaluate.report import print_screening
from risk_repository.evaluate.screen import (
    ScreeningComparison,
    compute_screening_metrics,
)
from risk_repository.screen import Decision
from risk_repository.settings import (
    DEFAULT_AIRTABLE_BASE_ID,
    DEFAULT_AIRTABLE_TIMEOUT,
)
from toolbox.airtable import AirtableClient, Table
from toolbox.log import configure_logging

logger = logging.getLogger(__name__)

DEFAULT_FULL_TEXT_SCREENING_TABLE = "Full-Text Screening"

_FIELDS = ["human_include_1", "human_include_2", "llm_include"]


class FullTextScreeningRow(BaseModel):
    record_id: str
    human_include_1: str | None = None
    human_include_2: str | None = None
    llm_include: str | None = None


class FullTextScreeningEvalSettings(
    BaseSettings,
    cli_parse_args=True,
    cli_kebab_case=True,
    cli_implicit_flags=True,
    cli_hide_none_type=True,
    cli_prog_name="risk_repository.evaluate.full_text_screen",
):
    """Evaluate full-text screening against human reviews in Airtable."""

    airtable_base_id: str = Field(
        default=DEFAULT_AIRTABLE_BASE_ID,
        description="Airtable ID for the AI Risk Repository base",
    )
    airtable_table: str = Field(
        default=DEFAULT_FULL_TEXT_SCREENING_TABLE,
        description="Airtable table holding full-text screening decisions",
    )
    airtable_timeout: float = Field(
        default=DEFAULT_AIRTABLE_TIMEOUT,
        description="Airtable API timeout in seconds",
    )


def _human_decision(value: str | None) -> Decision | None:
    """Map a reviewer's single-select to a decision, or None if undecided."""
    match value:
        case "Include":
            return Decision.INCLUDE
        case "Exclude":
            return Decision.EXCLUDE
        case _:
            return None


def _human_consensus(row: FullTextScreeningRow) -> Decision | None:
    """Combine the two reviewers into one ground-truth decision.

    Returns include/exclude when the deciding reviewers agree (or only one has
    decided), or None when neither has decided or the two disagree.
    """
    decisions = [
        d
        for d in (
            _human_decision(row.human_include_1),
            _human_decision(row.human_include_2),
        )
        if d is not None
    ]
    if not decisions or len(set(decisions)) > 1:
        return None
    return decisions[0]


def _pipeline_decision(value: str | None) -> Decision | None:
    match value:
        case "include":
            return Decision.INCLUDE
        case "exclude":
            return Decision.EXCLUDE
        case "uncertain":
            return Decision.UNCERTAIN
        case _:
            return None


async def fetch_comparisons(
    client: AirtableClient,
    *,
    base_id: str,
    table_name: str,
) -> list[ScreeningComparison]:
    table = Table(client, base_id=base_id, table_name=table_name)
    comparisons: list[ScreeningComparison] = []
    async for record in table.iterate(fields=_FIELDS):
        row = FullTextScreeningRow.model_validate(
            {"record_id": record.id, **record.fields}
        )
        ground_truth = _human_consensus(row)
        pipeline = _pipeline_decision(row.llm_include)
        if ground_truth is None or pipeline is None:
            continue
        comparisons.append(
            ScreeningComparison(
                readable_id=row.record_id,
                ground_truth=ground_truth,
                pipeline=pipeline,
            )
        )
    return comparisons


async def main() -> None:
    settings = FullTextScreeningEvalSettings()
    configure_logging(level=logging.INFO, loggers_to_silence=["httpx"])

    async with AirtableClient(timeout=settings.airtable_timeout) as client:
        comparisons = await fetch_comparisons(
            client,
            base_id=settings.airtable_base_id,
            table_name=settings.airtable_table,
        )
    logger.info(f"Comparable records (human decided, LLM scored): {len(comparisons)}")
    metrics = compute_screening_metrics(comparisons)
    print_screening(metrics, heading="Full-Text Screening")


if __name__ == "__main__":
    asyncio.run(main())
