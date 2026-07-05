import asyncio
import logging
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings

from risk_repository.results import PipelineStage, load, stage_dir
from risk_repository.screen import AbstractScreeningResult, Decision
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


class _StageConfig(BaseModel):
    pipeline_stage: PipelineStage
    text_source: str
    decision_rule: str


_STAGE_CONFIG: dict[ScreeningStage, _StageConfig] = {
    ScreeningStage.ABSTRACT: _StageConfig(
        pipeline_stage=PipelineStage.SCREEN_ABSTRACT,
        text_source="abstract",
        decision_rule="Single abstract screen",
    ),
    ScreeningStage.FULL_TEXT: _StageConfig(
        pipeline_stage=PipelineStage.SCREEN_FULL_TEXT,
        text_source="full_text",
        decision_rule="Single full-text screen",
    ),
}


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


def _screening_fields(
    result: AbstractScreeningResult,
    *,
    config: _StageConfig,
    model: str,
    prompt_version: str | None,
) -> dict[str, JsonValue]:
    fields: dict[str, JsonValue] = {
        "llm_include": result.decision.value,
        "llm_reasoning": result.criteria_breakdown,
        "n_screens": 1,
        "n_include": 1 if result.decision == Decision.INCLUDE else 0,
        "decision_rule": config.decision_rule,
        "screening_model_version": model,
        "text_source": config.text_source,
        "screening_status": "screened",
        "screened_at": datetime.now(UTC).isoformat(),
    }
    if prompt_version is not None:
        fields["screening_prompt_version"] = prompt_version
    return fields


def _load_decisions(
    run_dir: Path,
    pipeline_stage: PipelineStage,
) -> list[tuple[str, AbstractScreeningResult]]:
    """Load (record_id, result) pairs from a run's screening results."""
    results_dir = stage_dir(run_dir, pipeline_stage)
    if not results_dir.is_dir():
        raise FileNotFoundError(
            f"No {pipeline_stage.value} results directory in {run_dir}"
        )
    decisions = [
        (path.stem, load(path, AbstractScreeningResult))
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


async def _existing_record_ids(table: Table) -> set[str]:
    return {record.id async for record in table.iterate()}


async def upload_screening_decisions(
    table: Table,
    decisions: list[tuple[str, AbstractScreeningResult]],
    *,
    config: _StageConfig,
    model: str,
    prompt_version: str | None,
    dry_run: bool,
) -> None:
    existing = await _existing_record_ids(table)
    missing = sorted(
        record_id for record_id, _ in decisions if record_id not in existing
    )
    if missing:
        raise ValueError(
            f"{len(missing)} records do not exist in the table (e.g. {missing[0]!r});"
            + " upload only updates existing records"
        )
    updates = [
        UpdateRecord(
            id=record_id,
            fields=_screening_fields(
                result, config=config, model=model, prompt_version=prompt_version
            ),
        )
        for record_id, result in decisions
    ]
    if dry_run:
        logger.info(f"Dry run: would update {len(updates)} records")
        return
    await table.batch_update(updates, typecast=True)
    logger.info(f"Updated {len(updates)} records")


async def main() -> None:
    settings = UploadSettings()
    configure_logging(level=logging.INFO, loggers_to_silence=["httpx"])
    config = _STAGE_CONFIG[settings.stage]
    decisions = _load_decisions(settings.run_dir, config.pipeline_stage)
    logger.info(
        f"Loaded {len(decisions)} {settings.stage.value} decisions from"
        + f" {settings.run_dir}"
    )
    async with AirtableClient(timeout=settings.airtable_timeout) as client:
        table = Table(
            client,
            base_id=settings.airtable_base_id,
            table_name=settings.table,
        )
        await upload_screening_decisions(
            table,
            decisions,
            config=config,
            model=settings.model,
            prompt_version=settings.prompt_version,
            dry_run=settings.dry_run,
        )


if __name__ == "__main__":
    asyncio.run(main())
