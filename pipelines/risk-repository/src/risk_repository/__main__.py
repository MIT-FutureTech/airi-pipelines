import argparse
import asyncio
import logging
from collections.abc import Container
from pathlib import Path

from risk_repository.classify import (
    ClassificationResult,
    ClassifiedRisk,
    classify_causal,
)
from risk_repository.extract import ExtractionResult, extract_risks
from risk_repository.records import DocumentRecord, download_paper, fetch_records
from risk_repository.results import (
    STAGE_ORDER,
    PipelineStage,
    invalidate_downstream,
    load,
    result_path,
    save,
)
from risk_repository.screen import Decision, ScreeningResult, screen_document
from toolbox.airtable import Client as AirtableClient
from toolbox.concurrency import concurrent_map
from toolbox.llm import OpenAIClient
from toolbox.log import configure_logging
from toolbox.text_processing.pdf import convert_to_markdown

logger = logging.getLogger(__name__)

DEFAULT_CACHE_DIR = Path("cache/papers")
DEFAULT_OUTPUT_DIR = Path("output")
DEFAULT_MODEL = "gpt-5-mini-2025-08-07"
DEFAULT_CONCURRENCY = 5
LLM_RATE_LIMIT_RPS = 10.0
LLM_TIMEOUT = 180.0
AIRTABLE_TIMEOUT = 30.0

Document = tuple[DocumentRecord, Path]


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="AI Risk Repository pipeline")
    parser.add_argument("--cache-dir", type=Path, default=DEFAULT_CACHE_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--documents", nargs="+", default=None)
    parser.add_argument(
        "--stages",
        nargs="+",
        type=PipelineStage,
        choices=[stage.value for stage in STAGE_ORDER],
        default=[stage.value for stage in STAGE_ORDER],
    )
    parser.add_argument("--force", action="store_true")
    return parser.parse_args()


async def _collect_records(
    airtable: AirtableClient,
    document_ids: Container[str] | None,
    limit: int | None,
) -> list[DocumentRecord]:
    records: list[DocumentRecord] = []
    async for record in fetch_records(airtable):
        if document_ids is not None and record.quick_ref not in document_ids:
            continue
        records.append(record)
        if limit is not None and len(records) >= limit:
            break
    logger.info(f"Fetched {len(records)} records")
    return records


async def _download_all(
    records: list[DocumentRecord],
    cache_dir: Path,
) -> list[Document]:
    async def download_one(record: DocumentRecord) -> Document | None:
        pdf_path = await download_paper(record, cache_dir)
        if pdf_path is None:
            return None
        return record, pdf_path

    documents: list[Document] = []
    async for result in concurrent_map(records, download_one, DEFAULT_CONCURRENCY):
        if result is not None:
            documents.append(result)
    logger.info(f"Downloaded {len(documents)} PDFs")
    return documents


async def _screen_all(
    documents: list[Document],
    *,
    llm: OpenAIClient,
    output_dir: Path,
    force: bool,
) -> None:
    async def screen_one(doc: Document) -> None:
        record, pdf_path = doc
        output_path = result_path(output_dir, PipelineStage.SCREEN, record.quick_ref)
        if not force and output_path.exists():
            return
        first_page = convert_to_markdown(pdf_path, pages=[0])
        full_text = convert_to_markdown(pdf_path)
        screening = await screen_document(llm, first_page, full_text)
        save(output_path, screening)
        invalidate_downstream(output_dir, PipelineStage.SCREEN, record.quick_ref)
        logger.info(f"Screened {record.quick_ref}: {screening.decision}")

    async for _ in concurrent_map(documents, screen_one, DEFAULT_CONCURRENCY):
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
    *,
    llm: OpenAIClient,
    output_dir: Path,
    force: bool,
) -> None:
    async def extract_one(doc: Document) -> None:
        record, pdf_path = doc
        output_path = result_path(output_dir, PipelineStage.EXTRACT, record.quick_ref)
        if not force and output_path.exists():
            return
        full_text = convert_to_markdown(pdf_path)
        extraction = await extract_risks(llm, full_text)
        save(output_path, extraction)
        invalidate_downstream(output_dir, PipelineStage.EXTRACT, record.quick_ref)
        logger.info(f"Extracted {len(extraction.risks)} risks from {record.quick_ref}")

    async for _ in concurrent_map(documents, extract_one, DEFAULT_CONCURRENCY):
        pass


async def _classify_all(
    documents: list[Document],
    *,
    llm: OpenAIClient,
    output_dir: Path,
    force: bool,
) -> None:
    async def classify_one(doc: Document) -> None:
        record, _ = doc
        classify_path = result_path(
            output_dir, PipelineStage.CLASSIFY, record.quick_ref
        )
        if not force and classify_path.exists():
            return
        extract_path = result_path(output_dir, PipelineStage.EXTRACT, record.quick_ref)
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

    async for _ in concurrent_map(documents, classify_one, DEFAULT_CONCURRENCY):
        pass


async def amain() -> None:
    args = _parse_args()
    configure_logging(level=logging.INFO, loggers_to_silence=["httpx", "openai"])
    stages: set[PipelineStage] = set(args.stages)

    async with (
        AirtableClient(timeout=AIRTABLE_TIMEOUT) as airtable,
        OpenAIClient(
            model=args.model,
            rate_limit_rps=LLM_RATE_LIMIT_RPS,
            timeout=LLM_TIMEOUT,
        ) as llm,
    ):
        records = await _collect_records(airtable, args.documents, args.limit)
        documents = await _download_all(records, args.cache_dir)

        if PipelineStage.SCREEN in stages:
            await _screen_all(
                documents, llm=llm, output_dir=args.output_dir, force=args.force
            )
        documents = _filter_screened(documents, args.output_dir)

        if PipelineStage.EXTRACT in stages:
            await _extract_all(
                documents, llm=llm, output_dir=args.output_dir, force=args.force
            )

        if PipelineStage.CLASSIFY in stages:
            await _classify_all(
                documents, llm=llm, output_dir=args.output_dir, force=args.force
            )


if __name__ == "__main__":
    asyncio.run(amain())
