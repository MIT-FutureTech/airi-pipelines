import logging
from collections.abc import AsyncIterator
from datetime import date
from pathlib import Path
from typing import ClassVar

import httpx
from pydantic import BaseModel, ConfigDict, Field

from risk_repository.results import PipelineStage, stage_dir
from toolbox.airtable import Client, Table

BASE_ID = "app32FOUBa5WcUfEO"
TABLE_NAME = "Documents"

logger = logging.getLogger(__name__)


class DocumentRecord(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(populate_by_name=True)

    record_id: str
    paper_id: int | None = Field(None, validation_alias="PaperID")
    title: str = Field(validation_alias="DocTitle")
    authors: str = Field(validation_alias="DocAuthors")
    authors_short: str | None = Field(None, validation_alias="DocAuthors_Short")
    published_date: date | None = Field(None, validation_alias="PublishedDate")
    doi: str | None = Field(None, validation_alias="DOI")
    url: str | None = Field(None, validation_alias="URL")
    citations: int | None = Field(None, validation_alias="Citations")
    doc_type: str | None = Field(None, validation_alias="DocType")
    quick_ref: str = Field(validation_alias="QuickRef")


async def fetch_records(client: Client) -> AsyncIterator[DocumentRecord]:
    table = Table(client, BASE_ID, TABLE_NAME)
    async for record in table.iterate():
        yield DocumentRecord.model_validate({"record_id": record.id, **record.fields})


async def download_paper(
    record: DocumentRecord,
    output_dir: Path,
) -> Path | None:
    download_cache = stage_dir(output_dir, PipelineStage.COLLECT)
    cached = list(download_cache.glob(f"{record.quick_ref}.*"))
    if len(cached) == 1:
        logger.debug(f"Cache hit: {cached[0]}")
        return cached[0]

    if (url := record.url) is None:
        logger.warning(f"Paper {record.quick_ref} is missing a URL")
        return None
    url = url.replace("https://arxiv.org/abs/", "https://arxiv.org/pdf/")

    download_cache.mkdir(parents=True, exist_ok=True)
    async with httpx.AsyncClient(
        follow_redirects=True,
        headers={
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:149.0) Gecko/20100101 Firefox/149.0"
        },
    ) as http:
        response = await http.get(url)
        if response.status_code in {403, 404}:
            logger.warning(
                f"Skipping {record.quick_ref} due to fetch error: {response.status_code}"
            )
            logger.debug(f"Request for {url} returned response\n{response.text}")
            return None
        response.raise_for_status()
    content_type = response.headers.get("content-type", "").split(";")[0].strip()
    if content_type != "application/pdf":
        logger.warning(f"Skipping {record.quick_ref}: expected PDF, got {content_type}")
        return None

    local_path = download_cache / f"{record.quick_ref}.pdf"
    local_path.write_bytes(response.content)
    logger.info(f"Downloaded {record.url} -> {local_path}")
    return local_path
