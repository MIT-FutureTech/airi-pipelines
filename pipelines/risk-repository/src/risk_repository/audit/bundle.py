import logging
from collections.abc import AsyncIterator
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path

import httpx
from pydantic import BaseModel

from risk_repository.audit.settings import AuditSettings
from risk_repository.documents import format_abstract_and_title
from risk_repository.evaluate.ground_truth import fetch_ground_truth_documents
from risk_repository.evaluate.screen import (
    is_positive_ground_truth,
    is_positive_pipeline,
)
from risk_repository.records import (
    DocumentRecord,
    fetch_records_from_airtable,
    fetch_records_from_csv,
)
from risk_repository.results import PipelineStage, load, result_path
from risk_repository.screen import Decision, ScreeningResult
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
    abstract_result: ScreeningResult | None
    full_text_result: ScreeningResult | None
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
    airtable: AirtableClient | None,
    http_client: httpx.AsyncClient,
) -> AuditBundle:
    ground_truth = await _load_ground_truth(settings, airtable)
    documents: list[AuditDocument] = []
    skipped = 0
    async for record in _iter_records(settings, airtable):
        document = await _build_document(
            record,
            results_dir=settings.results_dir,
            download_cache_dir=settings.download_cache_dir,
            http_client=http_client,
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
    airtable: AirtableClient | None,
) -> dict[str, Decision | None]:
    if settings.ground_truth_table is None:
        return {}
    if airtable is None:
        raise ValueError("Ground-truth table requested but no Airtable client provided")
    docs = await fetch_ground_truth_documents(
        client=airtable,
        base_id=settings.airtable_base_id,
        documents_table_name=settings.ground_truth_table,
    )
    return {doc.readable_id: doc.screening_result for doc in docs}


async def _iter_records(
    settings: AuditSettings,
    airtable: AirtableClient | None,
) -> AsyncIterator[DocumentRecord]:
    if settings.csv_path is not None:
        async for record in fetch_records_from_csv(settings.csv_path):
            yield record
        return
    if airtable is None:
        raise ValueError("Airtable source requested but no Airtable client provided")
    if settings.airtable_documents_table is None:
        raise ValueError("Airtable source requested but no table name provided")
    async for record in fetch_records_from_airtable(
        airtable,
        base_id=settings.airtable_base_id,
        table_name=settings.airtable_documents_table,
    ):
        yield record


async def _build_document(
    record: DocumentRecord,
    *,
    results_dir: Path,
    download_cache_dir: Path,
    http_client: httpx.AsyncClient,
    ground_truth: dict[str, Decision | None],
) -> AuditDocument | None:
    abstract_result: ScreeningResult | None = None
    abstract_path = result_path(
        output_dir=results_dir,
        stage=PipelineStage.SCREEN_ABSTRACT,
        readable_id=record.readable_id,
    )
    if abstract_path.exists():
        abstract_result = load(abstract_path, ScreeningResult)
    full_text_path = result_path(
        output_dir=results_dir,
        stage=PipelineStage.SCREEN_FULL_TEXT,
        readable_id=record.readable_id,
    )
    full_text_result: ScreeningResult | None = None
    if full_text_path.exists():
        full_text_result = load(full_text_path, ScreeningResult)
    if abstract_result is None and full_text_result is None:
        return None

    abstract = record.abstract
    if abstract is None:
        abstract = await format_abstract_and_title(
            record=record,
            cache_dir=download_cache_dir,
            client=http_client,
        )
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
        abstract=abstract,
        screening=screening,
    )


def _compute_outcome(
    *,
    abstract_result: ScreeningResult | None,
    full_text_result: ScreeningResult | None,
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
