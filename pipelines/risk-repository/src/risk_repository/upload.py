import asyncio
import logging
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings

from risk_repository.results import PipelineStage, load, stage_dir
from risk_repository.screen import (
    AbstractScreeningResult,
    Decision,
    FullTextScreeningResult,
)
from risk_repository.settings import (
    DEFAULT_AIRTABLE_BASE_ID,
    DEFAULT_AIRTABLE_TIMEOUT,
    DEFAULT_MODEL,
)
from toolbox.airtable import AirtableClient, JsonValue, Table, UpdateRecord
from toolbox.log import configure_logging

logger = logging.getLogger(__name__)


class ScreeningStage(StrEnum):
    ABSTRACT = "abstract"
    FULL_TEXT = "full-text"


class UploadSettings(
    BaseSettings,
    cli_parse_args=True,
    cli_enforce_required=True,
    cli_kebab_case=True,
    cli_implicit_flags=True,
    cli_hide_none_type=True,
    cli_prog_name="risk_repository.upload",
):
    """
    Upload screening decisions from a pipeline run to an Airtable screening table.

    Reads the local screening results in the run directory and writes each
    decision onto the matching record in the screening table. Records must
    already exist in Airtable.
    """

    run_dir: Path = Field(
        default=...,
        description="Pipeline output directory containing screening results",
    )
    stage: ScreeningStage = Field(
        default=...,
        description="Which screening stage's results to upload",
    )
    table: str = Field(
        default=...,
        description="Airtable screening table to update",
    )
    model: str = Field(
        default=DEFAULT_MODEL,
        description="Model label recorded as screening_model_version",
    )
    prompt_version: str | None = Field(
        default=None,
        description="Prompt version label recorded as screening_prompt_version",
    )
    airtable_base_id: str = Field(
        default=DEFAULT_AIRTABLE_BASE_ID,
        description="Airtable ID for the AI Risk Repository base",
    )
    airtable_timeout: float = Field(
        default=DEFAULT_AIRTABLE_TIMEOUT,
        description="Airtable API timeout in seconds",
    )
    dry_run: bool = Field(
        default=False,
        description="Log what would be updated without writing to Airtable",
    )


def _common_fields(
    criteria_breakdown: str,
    *,
    text_source: str,
    model: str,
    prompt_version: str | None,
) -> dict[str, JsonValue]:
    fields: dict[str, JsonValue] = {
        "llm_reasoning": criteria_breakdown,
        "screening_model_version": model,
        "text_source": text_source,
        "screening_status": "screened",
        "screened_at": datetime.now(UTC).isoformat(),
    }
    if prompt_version is not None:
        fields["screening_prompt_version"] = prompt_version
    return fields


def _abstract_screening_fields(
    result: AbstractScreeningResult,
    *,
    model: str,
    prompt_version: str | None,
) -> dict[str, JsonValue]:
    return {
        **_common_fields(
            result.criteria_breakdown,
            text_source="abstract",
            model=model,
            prompt_version=prompt_version,
        ),
        "llm_include": result.decision.value,
        "n_screens": 1,
        "n_include": 1 if result.decision == Decision.INCLUDE else 0,
        "decision_rule": "Single abstract screen",
    }


def _full_text_screening_fields(
    result: FullTextScreeningResult,
    *,
    model: str,
    prompt_version: str | None,
) -> dict[str, JsonValue]:
    return {
        **_common_fields(
            result.criteria_breakdown,
            text_source="full_text",
            model=model,
            prompt_version=prompt_version,
        ),
        "llm_relevance_score": result.predicted_include_count,
    }


def _load_decisions[T: BaseModel](
    run_dir: Path,
    pipeline_stage: PipelineStage,
    result_type: type[T],
) -> list[tuple[str, T]]:
    """Load (record_id, result) pairs from a run's screening results."""
    results_dir = stage_dir(run_dir, pipeline_stage)
    if not results_dir.is_dir():
        raise FileNotFoundError(
            f"No {pipeline_stage.value} results directory in {run_dir}"
        )
    decisions = [
        (path.stem, load(path, result_type))
        for path in sorted(results_dir.glob("*.json"))
    ]
    non_record_ids = [record_id for record_id, _ in decisions if record_id[:3] != "rec"]
    if non_record_ids:
        raise ValueError(
            f"{len(non_record_ids)} result files are not named by an Airtable record"
            + f" ID (e.g. {non_record_ids[0]!r}). Upload requires a run screened from"
            + " a screening table, where each result's ID is its Airtable record ID."
        )
    return decisions


def _build_updates(
    run_dir: Path,
    stage: ScreeningStage,
    *,
    model: str,
    prompt_version: str | None,
) -> list[UpdateRecord]:
    match stage:
        case ScreeningStage.ABSTRACT:
            abstract = _load_decisions(
                run_dir, PipelineStage.SCREEN_ABSTRACT, AbstractScreeningResult
            )
            return [
                UpdateRecord(
                    id=record_id,
                    fields=_abstract_screening_fields(
                        result, model=model, prompt_version=prompt_version
                    ),
                )
                for record_id, result in abstract
            ]
        case ScreeningStage.FULL_TEXT:
            full_text = _load_decisions(
                run_dir, PipelineStage.SCREEN_FULL_TEXT, FullTextScreeningResult
            )
            return [
                UpdateRecord(
                    id=record_id,
                    fields=_full_text_screening_fields(
                        result, model=model, prompt_version=prompt_version
                    ),
                )
                for record_id, result in full_text
            ]


async def _existing_record_ids(table: Table) -> set[str]:
    return {record.id async for record in table.iterate()}


async def upload_screening_decisions(
    table: Table,
    updates: list[UpdateRecord],
    *,
    dry_run: bool,
) -> None:
    existing = await _existing_record_ids(table)
    missing = sorted(update.id for update in updates if update.id not in existing)
    if missing:
        raise ValueError(
            f"{len(missing)} records do not exist in the table (e.g. {missing[0]!r});"
            + " upload only updates existing records"
        )
    if dry_run:
        logger.info(f"Dry run: would update {len(updates)} records")
        return
    await table.batch_update(updates, typecast=True)
    logger.info(f"Updated {len(updates)} records")


async def main() -> None:
    settings = UploadSettings()
    configure_logging(level=logging.INFO, loggers_to_silence=["httpx"])
    updates = _build_updates(
        settings.run_dir,
        settings.stage,
        model=settings.model,
        prompt_version=settings.prompt_version,
    )
    logger.info(
        f"Loaded {len(updates)} {settings.stage.value} decisions from"
        + f" {settings.run_dir}"
    )
    async with AirtableClient(timeout=settings.airtable_timeout) as client:
        table = Table(
            client,
            base_id=settings.airtable_base_id,
            table_name=settings.table,
        )
        await upload_screening_decisions(table, updates, dry_run=settings.dry_run)


if __name__ == "__main__":
    asyncio.run(main())
