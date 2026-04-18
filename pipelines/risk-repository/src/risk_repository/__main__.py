import asyncio
import logging
from pathlib import Path

from risk_repository.classify import (
    ClassificationResult,
    ClassifiedRisk,
    classify_causal,
)
from risk_repository.extract import ExtractionResult, extract_risks
from risk_repository.records import DocumentRecord, download_paper, fetch_records
from risk_repository.results import (
    PipelineStage,
    invalidate_downstream,
    load,
    result_path,
    save,
)
from risk_repository.screen import Decision, ScreeningResult, screen_document
from risk_repository.settings import RiskRepositorySettings
from toolbox.airtable import Client as AirtableClient
from toolbox.concurrency import concurrent_map
from toolbox.llm import OpenAIClient
from toolbox.log import configure_logging
from toolbox.text_processing.pdf import convert_to_markdown

logger = logging.getLogger(__name__)

Document = tuple[DocumentRecord, Path]


async def _collect_records(
    airtable: AirtableClient,
    settings: RiskRepositorySettings,
) -> list[DocumentRecord]:
    docs_to_process = settings.document_ids
    records: list[DocumentRecord] = []
    async for record in fetch_records(
        client=airtable,
        base_id=settings.airtable_base_id,
        table_name=settings.airtable_table_name,
    ):
        if docs_to_process is not None and record.quick_ref not in docs_to_process:
            continue
        records.append(record)
        if settings.limit is not None and len(records) >= settings.limit:
            break
    logger.info(f"Fetched {len(records)} records")
    return records


async def _download_all(
    records: list[DocumentRecord],
    settings: RiskRepositorySettings,
) -> list[Document]:
    async def download_one(record: DocumentRecord) -> Document | None:
        pdf_path = await download_paper(record, settings.output_dir)
        if pdf_path is None:
            return None
        return record, pdf_path

    documents: list[Document] = []
    async for result in concurrent_map(
        items=records,
        func=download_one,
        max_concurrency=settings.concurrency,
        progress_description="Downloading",
    ):
        if result is not None:
            documents.append(result)
    logger.info(f"Downloaded {len(documents)} PDFs")
    return documents


async def _screen_all(
    documents: list[Document],
    llm: OpenAIClient,
    settings: RiskRepositorySettings,
) -> None:
    async def screen_one(doc: Document) -> None:
        record, pdf_path = doc
        output_path = result_path(
            settings.output_dir, PipelineStage.SCREEN, record.quick_ref
        )
        if not settings.force and output_path.exists():
            return
        first_page = convert_to_markdown(pdf_path, pages=[0])
        full_text = convert_to_markdown(pdf_path)
        screening = await screen_document(
            client=llm,
            first_page=first_page,
            full_text=full_text,
        )
        save(output_path, screening)
        invalidate_downstream(
            settings.output_dir, PipelineStage.SCREEN, record.quick_ref
        )
        logger.info(f"Screened {record.quick_ref}: {screening.decision}")

    async for _ in concurrent_map(
        items=documents,
        func=screen_one,
        max_concurrency=settings.concurrency,
        progress_description="Screening",
    ):
        pass


def _filter_screened(
    documents: list[Document],
    output_dir: Path,
) -> list[Document]:
    included: list[Document] = []
    for record, pdf_path in documents:
        output_path = result_path(output_dir, PipelineStage.SCREEN, record.quick_ref)
        if not output_path.exists():
            logger.warning(f"Skipping {record.quick_ref}: no screening results")
            continue
        screening = load(output_path, ScreeningResult)
        if screening.decision == Decision.EXCLUDE:
            continue
        included.append((record, pdf_path))
    logger.info(f"{len(included)} records passed screening")
    return included


async def _extract_all(
    documents: list[Document],
    llm: OpenAIClient,
    settings: RiskRepositorySettings,
) -> None:
    async def extract_one(doc: Document) -> None:
        record, pdf_path = doc
        output_path = result_path(
            settings.output_dir, PipelineStage.EXTRACT, record.quick_ref
        )
        if not settings.force and output_path.exists():
            return
        full_text = convert_to_markdown(pdf_path)
        extraction = await extract_risks(llm, full_text)
        save(output_path, extraction)
        invalidate_downstream(
            settings.output_dir, PipelineStage.EXTRACT, record.quick_ref
        )
        logger.info(f"Extracted {len(extraction.risks)} risks from {record.quick_ref}")

    async for _ in concurrent_map(
        items=documents,
        func=extract_one,
        max_concurrency=settings.concurrency,
        progress_description="Extracting",
    ):
        pass


async def _classify_all(
    documents: list[Document],
    llm: OpenAIClient,
    settings: RiskRepositorySettings,
) -> None:
    async def classify_one(doc: Document) -> None:
        record, _ = doc
        classify_path = result_path(
            settings.output_dir, PipelineStage.CLASSIFY, record.quick_ref
        )
        if not settings.force and classify_path.exists():
            return
        extract_path = result_path(
            settings.output_dir, PipelineStage.EXTRACT, record.quick_ref
        )
        if not extract_path.exists():
            logger.warning(f"Skipping {record.quick_ref}: no extraction results")
            return
        extraction = load(extract_path, ExtractionResult)
        classified_risks: list[ClassifiedRisk] = []
        for i, risk in enumerate(extraction.risks):
            risk_id = f"{record.quick_ref}-{i:03}"
            causal = await classify_causal(llm, risk)
            logger.info(
                f"Classified risk {risk_id} as {causal.model_dump_json(exclude={'reasoning'})}"
            )
            classified_risks.append(ClassifiedRisk(risk_id=risk_id, causal=causal))
        classification = ClassificationResult(risks=classified_risks)
        save(classify_path, classification)
        logger.info(f"Classified {len(classified_risks)} risks from {record.quick_ref}")

    async for _ in concurrent_map(
        items=documents,
        func=classify_one,
        max_concurrency=settings.concurrency,
        progress_description="Classifying",
    ):
        pass


async def amain() -> None:
    settings = RiskRepositorySettings()
    configure_logging(level=logging.INFO, loggers_to_silence=["httpx", "openai"])
    stages: set[PipelineStage] = set(settings.stages)

    async with (
        AirtableClient(timeout=settings.airtable_timeout) as airtable,
        OpenAIClient(
            model=settings.model,
            rate_limit_rps=settings.llm_rate_limit_rps,
            timeout=settings.llm_timeout,
        ) as llm,
    ):
        records = await _collect_records(airtable, settings)
        documents = await _download_all(records, settings)

        if PipelineStage.SCREEN in stages:
            await _screen_all(documents, llm, settings)
        documents = _filter_screened(documents, output_dir=settings.output_dir)

        if PipelineStage.EXTRACT in stages:
            await _extract_all(documents, llm, settings)

        if PipelineStage.CLASSIFY in stages:
            await _classify_all(documents, llm, settings)


if __name__ == "__main__":
    asyncio.run(amain())
