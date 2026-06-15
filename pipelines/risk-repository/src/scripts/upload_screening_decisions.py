#!/usr/bin/env python3
import argparse
import asyncio
import logging
from pathlib import Path

from pydantic import BaseModel, Field

from risk_repository.records import fetch_records_from_airtable
from risk_repository.results import PipelineStage, load, stage_dir
from risk_repository.screen import ScreeningResult
from risk_repository.settings import (
    DEFAULT_AIRTABLE_BASE_ID,
    DEFAULT_AIRTABLE_TIMEOUT,
)
from toolbox.airtable import AirtableClient, Table

logger = logging.getLogger(__name__)

DOCUMENTS_TABLE = "Documents 2026"
DECISIONS_TABLE = "Documents 2026 Screening Decisions"

_STAGES: dict[str, tuple[PipelineStage, str]] = {
    "abstract": (PipelineStage.SCREEN_ABSTRACT, "abstract"),
    "full-text": (PipelineStage.SCREEN_FULL_TEXT, "full text"),
}


class _DecisionRow(BaseModel):
    document: list[str] = Field(serialization_alias="Document")
    reviewer: str = Field(serialization_alias="Reviewer")
    stage: str = Field(serialization_alias="Stage")
    decision: str = Field(serialization_alias="Decision")
    run: str = Field(serialization_alias="Run")
    comments: str = Field(serialization_alias="Comments")


async def _document_index(
    client: AirtableClient,
    *,
    base_id: str,
    table_name: str,
) -> dict[str, str]:
    index: dict[str, str] = {}
    async for record in fetch_records_from_airtable(
        client,
        base_id=base_id,
        table_name=table_name,
    ):
        index[record.readable_id] = record.record_id
    return index


async def _documents_with_decision(
    table: Table,
    *,
    reviewer: str,
    stage_label: str,
) -> set[str]:
    formula = f'AND({{Reviewer}}="{reviewer}", {{Stage}}="{stage_label}")'
    document_ids: set[str] = set()
    async for record in table.iterate(formula=formula, fields=["Document"]):
        linked = record.fields.get("Document")
        if isinstance(linked, list):
            document_ids.update(rid for rid in linked if isinstance(rid, str))
    return document_ids


def _build_rows(
    decisions_dir: Path,
    *,
    index: dict[str, str],
    already_uploaded: set[str],
    reviewer: str,
    stage_label: str,
    run_name: str,
) -> list[_DecisionRow]:
    rows: list[_DecisionRow] = []
    unmatched = 0
    skipped = 0
    for path in sorted(decisions_dir.glob("*.json")):
        readable_id = path.stem
        record_id = index.get(readable_id)
        if record_id is None:
            logger.warning(f"No {DOCUMENTS_TABLE} record for {readable_id!r}, skipping")
            unmatched += 1
            continue
        if record_id in already_uploaded:
            skipped += 1
            continue
        screening = load(path, ScreeningResult)
        rows.append(
            _DecisionRow(
                document=[record_id],
                reviewer=reviewer,
                stage=stage_label,
                decision=screening.decision.value,
                run=run_name,
                comments=screening.criteria_breakdown,
            )
        )
    logger.info(
        f"Prepared {len(rows)} new decisions for reviewer {reviewer!r};"
        + f" {skipped} already uploaded, {unmatched} unmatched"
    )
    return rows


async def run(
    *,
    run_dir: Path,
    variant: str,
    pipeline_stage: PipelineStage,
    stage_label: str,
    base_id: str,
    dry_run: bool,
) -> None:
    decisions_dir = stage_dir(run_dir, pipeline_stage)
    if not decisions_dir.is_dir():
        raise FileNotFoundError(f"No {pipeline_stage.value} directory in {run_dir}")

    reviewer = f"pipeline-{variant}"
    run_name = run_dir.name

    async with AirtableClient(timeout=DEFAULT_AIRTABLE_TIMEOUT) as client:
        index = await _document_index(
            client,
            base_id=base_id,
            table_name=DOCUMENTS_TABLE,
        )
        logger.info(f"Loaded {len(index)} documents from {DOCUMENTS_TABLE!r}")

        decisions = Table(client, base_id=base_id, table_name=DECISIONS_TABLE)
        already_uploaded = await _documents_with_decision(
            decisions,
            reviewer=reviewer,
            stage_label=stage_label,
        )

        rows = _build_rows(
            decisions_dir,
            index=index,
            already_uploaded=already_uploaded,
            reviewer=reviewer,
            stage_label=stage_label,
            run_name=run_name,
        )

        if dry_run:
            logger.info("Dry run: no records written")
            return
        if not rows:
            logger.info("Nothing to upload")
            return

        created = await decisions.batch_create(
            [row.model_dump(by_alias=True) for row in rows]
        )
        logger.info(f"Created {len(created)} decision records")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="""
            Upload pipeline screening decisions from a tuning run into Airtable.
        """
    )
    parser.add_argument(
        "run_dir",
        type=Path,
        help="Tuning run directory containing the screening stage results",
    )
    parser.add_argument(
        "--variant",
        required=True,
        help="Pipeline variant label; the reviewer name becomes 'pipeline-<variant>'",
    )
    parser.add_argument(
        "--stage",
        choices=sorted(_STAGES),
        default="abstract",
        help="Screening stage to upload (default: abstract)",
    )
    parser.add_argument(
        "--airtable-base-id",
        default=DEFAULT_AIRTABLE_BASE_ID,
        help=f"Airtable base ID (default: {DEFAULT_AIRTABLE_BASE_ID})",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Log what would be uploaded without writing to Airtable",
    )
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(levelname)s\t%(message)s")

    pipeline_stage, stage_label = _STAGES[args.stage]
    asyncio.run(
        run(
            run_dir=args.run_dir,
            variant=args.variant,
            pipeline_stage=pipeline_stage,
            stage_label=stage_label,
            base_id=args.airtable_base_id,
            dry_run=args.dry_run,
        )
    )


if __name__ == "__main__":
    main()
