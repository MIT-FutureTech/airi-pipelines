import asyncio
import logging
from collections.abc import AsyncIterator
from pathlib import Path

import httpx

from risk_repository.classify import (
    ClassificationResult,
    ClassifiedRisk,
    classify_causal,
    make_causal_classifier,
)
from risk_repository.extract import ExtractionResult, extract_risks
from risk_repository.records import (
    DocumentRecord,
    fetch_records_from_airtable,
    fetch_records_from_csv,
    include_record,
    make_http_client,
)
from risk_repository.results import (
    PipelineStage,
    invalidate_downstream,
    load,
    result_path,
    save,
)
from risk_repository.screen import (
    Decision,
    ScreeningResult,
    screen_abstract,
    screen_full_text,
)
from risk_repository.settings import RiskRepositorySettings
from toolbox.airtable import AirtableClient
from toolbox.concurrency import concurrent_map
from toolbox.llm import LLMClient, OpenRouterClient
from toolbox.log import configure_logging, install_log_context_filter, log_context

logger = logging.getLogger(__name__)


async def _collect_records(
    airtable: AirtableClient,
    settings: RiskRepositorySettings,
) -> list[DocumentRecord]:
    docs_to_process = settings.document_ids
    records: list[DocumentRecord] = []
    async for record in _iterate_source(airtable, settings):
        if include_record(record, docs_to_process, settings.split):
            records.append(record)
        if settings.limit is not None and len(records) >= settings.limit:
            break
    logger.info(f"Fetched {len(records)} records")
    return records


async def _iterate_source(
    airtable: AirtableClient,
    settings: RiskRepositorySettings,
) -> AsyncIterator[DocumentRecord]:
    if settings.csv_path is not None:
        async for record in fetch_records_from_csv(settings.csv_path):
            yield record
    else:
        assert settings.airtable_documents_table is not None
        async for record in fetch_records_from_airtable(
            client=airtable,
            base_id=settings.airtable_base_id,
            table_name=settings.airtable_documents_table,
        ):
            yield record


async def _prefetch_abstracts(
    records: list[DocumentRecord],
    http_client: httpx.AsyncClient,
    settings: RiskRepositorySettings,
) -> list[DocumentRecord]:
    async def fetch_one(record: DocumentRecord) -> DocumentRecord | None:
        abstract = await record.get_abstract(
            cache_dir=settings.download_cache_dir, client=http_client
        )
        return record if abstract is not None else None

    available: list[DocumentRecord] = []
    async for result in concurrent_map(
        items=records,
        func=fetch_one,
        max_concurrency=settings.concurrency,
        progress_description="Fetching abstracts",
    ):
        if result is not None:
            available.append(result)
    failed = len(records) - len(available)
    logger.info(f"Abstracts: {len(available)} ok, {failed} failed")
    if failed:
        logger.info(
            f"See {settings.download_cache_dir}/*.failed.json for failure details"
        )
    return available


async def _prefetch_full_text(
    records: list[DocumentRecord],
    http_client: httpx.AsyncClient,
    settings: RiskRepositorySettings,
) -> list[DocumentRecord]:
    async def fetch_one(record: DocumentRecord) -> DocumentRecord | None:
        pdf_path = await record.get_pdf(
            cache_dir=settings.download_cache_dir,
            client=http_client,
        )
        return record if pdf_path is not None else None

    available: list[DocumentRecord] = []
    async for result in concurrent_map(
        items=records,
        func=fetch_one,
        max_concurrency=settings.concurrency,
        progress_description="Fetching full texts",
    ):
        if result is not None:
            available.append(result)
    failed = len(records) - len(available)
    logger.info(f"Full texts: {len(available)} ok, {failed} failed")
    if failed:
        logger.info(
            f"See {settings.download_cache_dir}/*.failed.json for failure details"
        )
    return available


async def _screen_abstract_all(
    records: list[DocumentRecord],
    llm: LLMClient,
    http_client: httpx.AsyncClient,
    settings: RiskRepositorySettings,
) -> None:
    async def screen_one(record: DocumentRecord) -> None:
        with log_context(readable_id=record.readable_id):
            output_path = result_path(
                settings.output_dir,
                PipelineStage.SCREEN_ABSTRACT,
                record.readable_id,
            )
            if not settings.force and output_path.exists():
                return
            abstract = await record.get_abstract(
                cache_dir=settings.download_cache_dir,
                client=http_client,
            )
            if abstract is None:
                logger.warning("Skipping screening: no abstract available")
                return
            screening = await screen_abstract(llm, abstract)
            save(output_path, screening)
            invalidate_downstream(
                settings.output_dir,
                PipelineStage.SCREEN_ABSTRACT,
                record.readable_id,
            )
            logger.info(f"Abstract screening decision: {screening.decision}")

    async for _ in concurrent_map(
        items=records,
        func=screen_one,
        max_concurrency=settings.concurrency,
        progress_description="Screening abstracts",
    ):
        pass


async def _screen_full_text_all(
    records: list[DocumentRecord],
    llm: LLMClient,
    http_client: httpx.AsyncClient,
    settings: RiskRepositorySettings,
) -> None:
    async def screen_one(record: DocumentRecord) -> None:
        with log_context(readable_id=record.readable_id):
            output_path = result_path(
                settings.output_dir,
                PipelineStage.SCREEN_FULL_TEXT,
                record.readable_id,
            )
            if not settings.force and output_path.exists():
                return
            full_text = await record.get_full_text(
                cache_dir=settings.download_cache_dir,
                client=http_client,
                max_truncation_ratio=settings.document_max_truncation_ratio,
                max_document_length=settings.document_length_limit,
            )
            if full_text is None:
                logger.warning("Skipping screening: no full text available")
                return
            screening = await screen_full_text(llm, full_text)
            save(output_path, screening)
            invalidate_downstream(
                settings.output_dir,
                PipelineStage.SCREEN_FULL_TEXT,
                record.readable_id,
            )
            logger.info(f"Full-text screening decision: {screening.decision}")

    async for _ in concurrent_map(
        items=records,
        func=screen_one,
        max_concurrency=settings.concurrency,
        progress_description="Screening full texts",
    ):
        pass


def _filter_by_screening(
    records: list[DocumentRecord],
    output_dir: Path,
    stage: PipelineStage,
) -> list[DocumentRecord]:
    included: list[DocumentRecord] = []
    unscreened = 0
    for record in records:
        output_path = result_path(output_dir, stage, record.readable_id)
        if not output_path.exists():
            unscreened += 1
            included.append(record)
            continue
        screening = load(output_path, ScreeningResult)
        if screening.decision == Decision.EXCLUDE:
            continue
        included.append(record)
    if unscreened:
        logger.info(
            f"{unscreened}/{len(records)} records have no {stage.value} result;"
            + " passing through unfiltered"
        )
    logger.info(f"{len(included)} records passed {stage.value}")
    return included


async def _extract_all(
    records: list[DocumentRecord],
    llm: LLMClient,
    http_client: httpx.AsyncClient,
    settings: RiskRepositorySettings,
) -> None:
    async def extract_one(record: DocumentRecord) -> None:
        with log_context(readable_id=record.readable_id):
            output_path = result_path(
                settings.output_dir, PipelineStage.EXTRACT, record.readable_id
            )
            if not settings.force and output_path.exists():
                return
            full_text = await record.get_full_text(
                cache_dir=settings.download_cache_dir,
                client=http_client,
                max_truncation_ratio=settings.document_max_truncation_ratio,
                max_document_length=settings.document_length_limit,
            )
            if full_text is None:
                logger.warning("Skipping extraction: no full text available")
                return
            extraction = await extract_risks(llm, full_text)
            save(output_path, extraction)
            invalidate_downstream(
                settings.output_dir, PipelineStage.EXTRACT, record.readable_id
            )
            logger.info(f"Extracted {len(extraction.risks)} risks")

    async for _ in concurrent_map(
        items=records,
        func=extract_one,
        max_concurrency=settings.concurrency,
        progress_description="Extracting",
    ):
        pass


async def _classify_all(
    records: list[DocumentRecord],
    llm: LLMClient,
    settings: RiskRepositorySettings,
) -> None:
    classifier = make_causal_classifier(llm)

    async def classify_one(record: DocumentRecord) -> None:
        with log_context(readable_id=record.readable_id):
            classify_path = result_path(
                settings.output_dir, PipelineStage.CLASSIFY, record.readable_id
            )
            if not settings.force and classify_path.exists():
                return
            extract_path = result_path(
                settings.output_dir, PipelineStage.EXTRACT, record.readable_id
            )
            if not extract_path.exists():
                logger.warning("Skipping document: no extraction results")
                return
            extraction = load(extract_path, ExtractionResult)
            classified_risks: list[ClassifiedRisk] = []
            for i, risk in enumerate(extraction.risks):
                risk_id = f"{record.readable_id}-{i:03}"
                with log_context(risk_id=risk_id):
                    causal = await classify_causal(classifier, risk)
                    serialized = causal.model_dump_json(exclude={"reasoning"})
                    logger.info(f"Classified risk as {serialized}")
                classified_risks.append(ClassifiedRisk(risk_id=risk_id, causal=causal))
            classification = ClassificationResult(risks=classified_risks)
            save(classify_path, classification)
            logger.info(f"Classified {len(classified_risks)} risks")

    async for _ in concurrent_map(
        items=records,
        func=classify_one,
        max_concurrency=settings.concurrency,
        progress_description="Classifying",
    ):
        pass


async def main() -> None:
    settings = RiskRepositorySettings()
    configure_logging(
        level=logging.INFO,
        filepath=settings.log_path or settings.output_dir / "log.txt",
        loggers_to_silence=["httpx", "openai"],
    )
    try:
        install_log_context_filter()
        stages: set[PipelineStage] = set(settings.stages)

        async with (
            AirtableClient(timeout=settings.airtable_timeout) as airtable,
            OpenRouterClient(
                model=settings.model,
                rate_limit_rps=settings.llm_rate_limit_rps,
                timeout=settings.llm_timeout,
            ) as llm,
            make_http_client() as http_client,
        ):
            records = await _collect_records(airtable, settings)

            if PipelineStage.SCREEN_ABSTRACT in stages:
                records = await _prefetch_abstracts(records, http_client, settings)
                await _screen_abstract_all(records, llm, http_client, settings)
            records = _filter_by_screening(
                records, settings.output_dir, PipelineStage.SCREEN_ABSTRACT
            )

            full_text_prefetched = False
            if PipelineStage.SCREEN_FULL_TEXT in stages:
                records = await _prefetch_full_text(records, http_client, settings)
                full_text_prefetched = True
                await _screen_full_text_all(records, llm, http_client, settings)
            records = _filter_by_screening(
                records, settings.output_dir, PipelineStage.SCREEN_FULL_TEXT
            )

            if PipelineStage.EXTRACT in stages:
                if not full_text_prefetched:
                    records = await _prefetch_full_text(records, http_client, settings)
                await _extract_all(records, llm, http_client, settings)

            if PipelineStage.CLASSIFY in stages:
                await _classify_all(records, llm, settings)
    except:
        logger.exception("Uncaught exception")
        raise


if __name__ == "__main__":
    asyncio.run(main())
