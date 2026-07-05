import logging
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path

from pydantic import BaseModel

from risk_repository.audit.settings import AuditSettings
from risk_repository.evaluate.ground_truth import fetch_screening_ground_truth
from risk_repository.evaluate.screen import (
    is_positive_ground_truth,
    is_positive_pipeline,
)
from risk_repository.records import DocumentRecord, fetch_screening_records
from risk_repository.results import PipelineStage, load, result_path
from risk_repository.screen import AbstractScreeningResult, Decision
from toolbox.airtable import AirtableClient

logger = logging.getLogger(__name__)


class OutcomeClass(StrEnum):
    TRUE_POSITIVE = "true_positive"
    FALSE_POSITIVE = "false_positive"
    TRUE_NEGATIVE = "true_negative"
    FALSE_NEGATIVE = "false_negative"
    UNLABELED = "unlabeled"


class ScreeningAudit(BaseModel):
    ground_truth_decision: Decision | None
    abstract_result: AbstractScreeningResult | None
    full_text_result: AbstractScreeningResult | None
    outcome_class: OutcomeClass


class AuditDocument(BaseModel):
    readable_id: str
    title: str | None
    url: str | None
    pdf_path: Path | None
    abstract: str | None
    screening: ScreeningAudit


class AuditBundle(BaseModel):
    run_name: str | None
    results_dir: Path
    generated_at: datetime
    documents: list[AuditDocument]


async def assemble_bundle(
    settings: AuditSettings,
    *,
    airtable: AirtableClient,
) -> AuditBundle:
    ground_truth = await _load_ground_truth(settings, airtable)
    documents: list[AuditDocument] = []
    skipped = 0
    async for record in fetch_screening_records(
        airtable,
        base_id=settings.airtable_base_id,
        table_name=settings.airtable_screening_table,
    ):
        document = _build_document(
            record,
            results_dir=settings.results_dir,
            download_cache_dir=settings.download_cache_dir,
            ground_truth=ground_truth,
        )
        if document is None:
            skipped += 1
            continue
        documents.append(document)
    logger.info(
        f"Bundled {len(documents)} documents;"
        + f" skipped {skipped} without screening results"
    )
    return AuditBundle(
        run_name=settings.run_name,
        results_dir=settings.results_dir,
        generated_at=datetime.now(UTC),
        documents=documents,
    )


async def _load_ground_truth(
    settings: AuditSettings,
    airtable: AirtableClient,
) -> dict[str, Decision | None]:
    return await fetch_screening_ground_truth(
        client=airtable,
        base_id=settings.airtable_base_id,
        table_name=settings.airtable_screening_table,
    )


def _build_document(
    record: DocumentRecord,
    *,
    results_dir: Path,
    download_cache_dir: Path,
    ground_truth: dict[str, Decision | None],
) -> AuditDocument | None:
    abstract_result: AbstractScreeningResult | None = None
    abstract_path = result_path(
        output_dir=results_dir,
        stage=PipelineStage.SCREEN_ABSTRACT,
        readable_id=record.readable_id,
    )
    if abstract_path.exists():
        abstract_result = load(abstract_path, AbstractScreeningResult)
    full_text_path = result_path(
        output_dir=results_dir,
        stage=PipelineStage.SCREEN_FULL_TEXT,
        readable_id=record.readable_id,
    )
    full_text_result: AbstractScreeningResult | None = None
    if full_text_path.exists():
        full_text_result = load(full_text_path, AbstractScreeningResult)
    if abstract_result is None and full_text_result is None:
        return None

    pdf_cache = download_cache_dir / f"{record.readable_id}.pdf"
    pdf_path = pdf_cache.resolve() if pdf_cache.exists() else None
    gt_decision = ground_truth.get(record.readable_id)

    screening = ScreeningAudit(
        ground_truth_decision=gt_decision,
        abstract_result=abstract_result,
        full_text_result=full_text_result,
        outcome_class=_compute_outcome(
            abstract_result=abstract_result,
            full_text_result=full_text_result,
            gt_decision=gt_decision,
        ),
    )
    return AuditDocument(
        readable_id=record.readable_id,
        title=record.title,
        url=record.url,
        pdf_path=pdf_path,
        abstract=record.abstract,
        screening=screening,
    )


def _compute_outcome(
    *,
    abstract_result: AbstractScreeningResult | None,
    full_text_result: AbstractScreeningResult | None,
    gt_decision: Decision | None,
) -> OutcomeClass:
    if gt_decision is None:
        return OutcomeClass.UNLABELED
    latest = full_text_result if full_text_result is not None else abstract_result
    assert latest is not None
    pred_positive = is_positive_pipeline(latest.decision)
    gt_positive = is_positive_ground_truth(gt_decision)
    if pred_positive and gt_positive:
        return OutcomeClass.TRUE_POSITIVE
    if pred_positive and not gt_positive:
        return OutcomeClass.FALSE_POSITIVE
    if not pred_positive and gt_positive:
        return OutcomeClass.FALSE_NEGATIVE
    return OutcomeClass.TRUE_NEGATIVE
