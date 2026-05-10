import csv
import logging
from abc import ABCMeta, abstractmethod
from collections.abc import AsyncIterator, Container
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from typing import override

import httpx
from pydantic import BaseModel, Field

from toolbox.airtable import AirtableClient, Table
from toolbox.text_processing.markdown import truncate_at_heading
from toolbox.text_processing.pdf import convert_to_markdown

logger = logging.getLogger(__name__)


class TestTrainSplit(StrEnum):
    TRAIN = "train"
    TEST = "test"


class DocumentRecord(BaseModel, metaclass=ABCMeta):
    readable_id: str
    url: str | None
    split: TestTrainSplit | None = None

    @abstractmethod
    def _full_text_url(self) -> str | None: ...

    @abstractmethod
    async def get_abstract(
        self,
        *,
        cache_dir: Path,
        client: httpx.AsyncClient,
    ) -> str | None: ...

    async def get_pdf(
        self,
        *,
        cache_dir: Path,
        client: httpx.AsyncClient,
    ) -> Path | None:
        url = self._full_text_url()
        if url is None:
            logger.warning(f"{self.readable_id} has no URL to fetch full text")
            _record_failure(
                cache_dir=cache_dir,
                readable_id=self.readable_id,
                url=None,
                reason="record has no full-text URL",
                details=None,
            )
            return None
        return await download_pdf(
            url=url,
            cache_dir=cache_dir,
            readable_id=self.readable_id,
            client=client,
        )

    async def get_full_text(
        self,
        *,
        cache_dir: Path,
        client: httpx.AsyncClient,
        max_truncation_ratio: float,
        max_document_length: int,
    ) -> str | None:
        pdf_path = await self.get_pdf(cache_dir=cache_dir, client=client)
        if pdf_path is None:
            return None
        try:
            return _load_full_text(
                pdf_path,
                max_truncation_ratio=max_truncation_ratio,
                max_document_length=max_document_length,
            )
        except RuntimeError as error:
            logger.warning(f"Skipping {self.readable_id}: {error!r}")
            _record_failure(
                cache_dir=cache_dir,
                readable_id=self.readable_id,
                url=self._full_text_url(),
                reason=repr(error),
                details=None,
            )
            return None


class AirtableDocumentRecord(DocumentRecord):
    record_id: str
    readable_id: str = Field(validation_alias="QuickRef")
    url: str | None = Field(default=None, validation_alias="URL")
    split: TestTrainSplit | None = Field(default=None, validation_alias="Split")

    @override
    def _full_text_url(self) -> str | None:
        return self.url

    @override
    async def get_abstract(
        self,
        *,
        cache_dir: Path,
        client: httpx.AsyncClient,
    ) -> str | None:
        pdf_path = await self.get_pdf(cache_dir=cache_dir, client=client)
        if pdf_path is None:
            return None
        return convert_to_markdown(pdf_path, pages=[0])


class CsvDocumentRecord(DocumentRecord):
    title: str
    abstract: str
    doi: str | None = None
    url: str | None = Field(default=None, alias="link")
    author_keywords: str | None = None

    @override
    def _full_text_url(self) -> str | None:
        if self.doi:
            return f"https://doi.org/{self.doi}"
        return self.url

    @override
    async def get_abstract(
        self,
        *,
        cache_dir: Path,
        client: httpx.AsyncClient,
    ) -> str | None:
        del cache_dir, client
        sections = [f"# {self.title}", f"## Abstract\n\n{self.abstract}"]
        if self.author_keywords:
            sections.append(f"## Keywords\n\n{self.author_keywords}")
        return "\n\n".join(sections)


async def fetch_records_from_csv(csv_path: Path) -> AsyncIterator[CsvDocumentRecord]:
    with csv_path.open(newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            yield CsvDocumentRecord.model_validate(
                {"readable_id": f"csv-{int(row['id']):04d}", **row}
            )


async def fetch_records_from_airtable(
    client: AirtableClient,
    *,
    base_id: str,
    table_name: str,
) -> AsyncIterator[AirtableDocumentRecord]:
    table = Table(client, base_id=base_id, table_name=table_name)
    async for record in table.iterate():
        yield AirtableDocumentRecord.model_validate(
            {"record_id": record.id, **record.fields}
        )


def include_record(
    record: DocumentRecord,
    document_ids: Container[str] | None,
    split: TestTrainSplit,
) -> bool:
    if record.split is not None and record.split != split:
        return False
    if document_ids is None:
        return True
    return record.readable_id in document_ids


def make_http_client() -> httpx.AsyncClient:
    return httpx.AsyncClient(
        follow_redirects=True,
        headers={
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:149.0) Gecko/20100101 Firefox/149.0"
        },
    )


async def download_pdf(
    *,
    url: str,
    cache_dir: Path,
    readable_id: str,
    client: httpx.AsyncClient,
) -> Path | None:
    cached = cache_dir / f"{readable_id}.pdf"
    if cached.exists():
        logger.debug(f"Cache hit: {cached}")
        return cached

    fetch_url = url.replace("https://arxiv.org/abs/", "https://arxiv.org/pdf/")
    cache_dir.mkdir(parents=True, exist_ok=True)

    response = await client.get(fetch_url)
    if response.status_code in {403, 404}:
        logger.warning(
            f"Skipping {readable_id} due to fetch error: {response.status_code}"
        )
        logger.debug(f"Request for {fetch_url} returned response\n{response.text}")
        _record_failure(
            cache_dir=cache_dir,
            readable_id=readable_id,
            url=url,
            reason=f"HTTP {response.status_code}",
            details=response.text,
        )
        return None
    response.raise_for_status()
    content_type = response.headers.get("content-type", "").split(";")[0].strip()
    if content_type != "application/pdf":
        logger.warning(f"Skipping {readable_id}: expected PDF, got {content_type}")
        _record_failure(
            cache_dir=cache_dir,
            readable_id=readable_id,
            url=url,
            reason=f"expected PDF, got {content_type}",
            details=None,
        )
        return None

    cached.write_bytes(response.content)
    _clear_failure(cache_dir=cache_dir, readable_id=readable_id)
    logger.info(f"Downloaded {url} -> {cached}")
    return cached


class DownloadFailure(BaseModel):
    readable_id: str
    url: str | None
    reason: str
    details: str | None
    timestamp: datetime


def _failure_path(cache_dir: Path, readable_id: str) -> Path:
    return cache_dir / f"{readable_id}.failed.json"


def _record_failure(
    *,
    cache_dir: Path,
    readable_id: str,
    url: str | None,
    reason: str,
    details: str | None,
) -> None:
    cache_dir.mkdir(parents=True, exist_ok=True)
    failure = DownloadFailure(
        readable_id=readable_id,
        url=url,
        reason=reason,
        details=details,
        timestamp=datetime.now(UTC),
    )
    _failure_path(cache_dir, readable_id).write_text(failure.model_dump_json(indent=2))


def _clear_failure(*, cache_dir: Path, readable_id: str) -> None:
    path = _failure_path(cache_dir, readable_id)
    if path.exists():
        path.unlink()


def _load_full_text(
    pdf_path: Path,
    *,
    max_truncation_ratio: float,
    max_document_length: int,
) -> str:
    truncation = truncate_at_heading(convert_to_markdown(pdf_path))
    if truncation.truncation_ratio > max_truncation_ratio:
        raise RuntimeError(
            f"Truncation at {truncation.matched_heading!r}"
            + f" would remove {truncation.truncation_ratio:.1%}, "
            + f" exceeding {max_truncation_ratio:.1%}"
        )
    if len(truncation.text) > max_document_length:
        logger.info(
            "Document still exceeds maximum length after section truncation."
            + f" Reducing from {truncation.original_length:,d} to"
            + f" {max_document_length:,d} characters"
            + f" ({max_document_length / truncation.original_length:.1%} of original)."
        )
        truncation.text = truncation.text[:max_document_length]
    return truncation.text
