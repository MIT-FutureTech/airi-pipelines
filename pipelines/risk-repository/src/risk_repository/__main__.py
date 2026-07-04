import asyncio
import logging
from collections.abc import AsyncIterator

from risk_repository.classify import run_classification
from risk_repository.documents import (
    prefetch_abstracts,
    prefetch_full_text,
)
from risk_repository.download import make_http_client
from risk_repository.extract import run_extraction
from risk_repository.records import (
    DocumentRecord,
    FullTextScreeningRecord,
    fetch_full_text_screening_records,
    fetch_records_from_airtable,
    fetch_records_from_csv,
    include_record,
)
from risk_repository.results import PipelineStage
from risk_repository.screen import (
    filter_by_screening,
    run_abstract_screening,
    run_full_text_screening,
)
from risk_repository.settings import RiskRepositorySettings
from toolbox.airtable import AirtableClient
from toolbox.llm import OpenRouterClient
from toolbox.log import configure_logging, install_log_context_filter

logger = logging.getLogger(__name__)


async def _collect_records(
    airtable: AirtableClient,
    settings: RiskRepositorySettings,
) -> list[DocumentRecord]:
    docs_to_process = settings.document_ids
    records: list[DocumentRecord] = []
    skipped_no_pdf = 0
    async for record in _iterate_source(airtable, settings):
        if isinstance(record, FullTextScreeningRecord) and not record.has_pdf:
            skipped_no_pdf += 1
            continue
        if include_record(record, docs_to_process, settings.split):
            records.append(record)
        if settings.limit is not None and len(records) >= settings.limit:
            break
    if skipped_no_pdf:
        logger.info(f"Skipped {skipped_no_pdf} records with no attached PDF")
    logger.info(f"Fetched {len(records)} records")
    return records


async def _iterate_source(
    airtable: AirtableClient,
    settings: RiskRepositorySettings,
) -> AsyncIterator[DocumentRecord]:
    if settings.csv_path is not None:
        async for record in fetch_records_from_csv(settings.csv_path):
            yield record
    elif settings.airtable_full_text_table is not None:
        async for record in fetch_full_text_screening_records(
            client=airtable,
            base_id=settings.airtable_base_id,
            table_name=settings.airtable_full_text_table,
        ):
            yield record
    else:
        assert settings.airtable_documents_table is not None
        async for record in fetch_records_from_airtable(
            client=airtable,
            base_id=settings.airtable_base_id,
            table_name=settings.airtable_documents_table,
        ):
            yield record


async def main() -> None:
    settings = RiskRepositorySettings()
    settings.output_dir.mkdir(parents=True, exist_ok=True)
    settings.download_cache_dir.mkdir(parents=True, exist_ok=True)
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
                records = await prefetch_abstracts(
                    records,
                    cache_dir=settings.download_cache_dir,
                    client=http_client,
                    concurrency=settings.concurrency,
                )
                await run_abstract_screening(
                    records, llm=llm, http_client=http_client, settings=settings
                )
            records = filter_by_screening(
                records, settings=settings, stage=PipelineStage.SCREEN_ABSTRACT
            )

            full_text_prefetched = False
            if PipelineStage.SCREEN_FULL_TEXT in stages:
                records = await prefetch_full_text(
                    records,
                    cache_dir=settings.download_cache_dir,
                    client=http_client,
                    concurrency=settings.concurrency,
                )
                full_text_prefetched = True
                await run_full_text_screening(
                    records,
                    llm=llm,
                    http_client=http_client,
                    settings=settings,
                )
            records = filter_by_screening(
                records, settings=settings, stage=PipelineStage.SCREEN_FULL_TEXT
            )

            if PipelineStage.EXTRACT in stages:
                if not full_text_prefetched:
                    records = await prefetch_full_text(
                        records,
                        cache_dir=settings.download_cache_dir,
                        client=http_client,
                        concurrency=settings.concurrency,
                    )
                await run_extraction(
                    records, llm=llm, http_client=http_client, settings=settings
                )

            if PipelineStage.CLASSIFY in stages:
                await run_classification(records, llm=llm, settings=settings)
    except:
        logger.exception("Uncaught exception")
        raise


if __name__ == "__main__":
    asyncio.run(main())
