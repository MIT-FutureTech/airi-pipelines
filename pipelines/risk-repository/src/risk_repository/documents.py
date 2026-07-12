import logging
from pathlib import Path

import httpx

from risk_repository.download import clear_failure, download_pdf, record_failure
from risk_repository.records import DocumentRecord, ScreeningRecord
from toolbox.airtable import download_attachment
from toolbox.concurrency import ConcurrentMap
from toolbox.text_processing.pdf import convert_to_markdown

logger = logging.getLogger(__name__)


def format_abstract_and_title(record: DocumentRecord) -> str | None:
    if record.abstract is None:
        return None
    return f"# {record.title}\n\n## Abstract\n\n{record.abstract}"


async def get_pdf(
    record: DocumentRecord,
    *,
    cache_dir: Path,
    client: httpx.AsyncClient,
) -> Path | None:
    if isinstance(record, ScreeningRecord):
        return await _get_attachment_pdf(record, cache_dir=cache_dir, client=client)
    url = _full_text_url(record)
    if url is None:
        logger.warning(f"{record.readable_id} has no URL to fetch full text")
        record_failure(
            cache_dir=cache_dir,
            readable_id=record.readable_id,
            url=None,
            reason="record has no full-text URL",
            details=None,
        )
        return None
    return await download_pdf(
        url=url,
        cache_dir=cache_dir,
        readable_id=record.readable_id,
        client=client,
    )


async def _get_attachment_pdf(
    record: ScreeningRecord,
    *,
    cache_dir: Path,
    client: httpx.AsyncClient,
) -> Path | None:
    cached = cache_dir / f"{record.readable_id}.pdf"
    if cached.exists():
        logger.debug(f"Cache hit: {cached}")
        return cached
    if not record.has_pdf:
        logger.warning(f"{record.readable_id} has no PDF attachment")
        record_failure(
            cache_dir=cache_dir,
            readable_id=record.readable_id,
            url=None,
            reason="record has no PDF attachment",
            details=None,
        )
        return None
    attachment = record.attachments[0]
    content = await download_attachment(client, attachment)
    cached.write_bytes(content)
    clear_failure(cache_dir=cache_dir, readable_id=record.readable_id)
    logger.info(f"Downloaded attachment {attachment.filename} -> {cached}")
    return cached


async def get_full_text(
    record: DocumentRecord,
    *,
    cache_dir: Path,
    client: httpx.AsyncClient,
) -> str | None:
    pdf_path = await get_pdf(record, cache_dir=cache_dir, client=client)
    if pdf_path is None:
        return None
    try:
        return convert_to_markdown(pdf_path)
    except RuntimeError as error:
        logger.warning(f"Skipping {record.readable_id}: {error!r}")
        record_failure(
            cache_dir=cache_dir,
            readable_id=record.readable_id,
            url=_full_text_url(record),
            reason=repr(error),
            details=None,
        )
        return None


def select_records_with_abstract(records: list[DocumentRecord]) -> list[DocumentRecord]:
    available = [r for r in records if r.abstract is not None]
    skipped = len(records) - len(available)
    logger.info(f"Abstracts: {len(available)} available, {skipped} missing")
    return available


async def _prefetch_full_text_one(
    record: DocumentRecord,
    *,
    cache_dir: Path,
    client: httpx.AsyncClient,
) -> DocumentRecord | None:
    pdf_path = await get_pdf(record, cache_dir=cache_dir, client=client)
    return record if pdf_path is not None else None


async def prefetch_full_text(
    records: list[DocumentRecord],
    *,
    cache_dir: Path,
    client: httpx.AsyncClient,
    concurrency: int,
) -> list[DocumentRecord]:
    runner = ConcurrentMap(
        max_concurrency=concurrency, progress_description="Fetching full texts"
    )
    available: list[DocumentRecord] = []
    async for result in runner.map(
        records,
        _prefetch_full_text_one,
        cache_dir=cache_dir,
        client=client,
    ):
        if result is not None:
            available.append(result)
    failed = len(records) - len(available)
    logger.info(f"Full texts: {len(available)} ok, {failed} failed")
    if failed:
        logger.info(f"See {cache_dir}/*.failed.json for failure details")
    return available


def _full_text_url(record: DocumentRecord) -> str | None:
    match record:
        case ScreeningRecord():
            return record.url
        case _:
            raise TypeError(f"Unknown record type: {type(record).__name__}")
