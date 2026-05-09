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
    quick_ref: str
    split: TestTrainSplit

    @abstractmethod
    async def get_abstract(
        self,
        *,
        cache_dir: Path,
        client: httpx.AsyncClient,
    ) -> str | None: ...

    @abstractmethod
    async def get_full_text(
        self,
        *,
        cache_dir: Path,
        client: httpx.AsyncClient,
        max_truncation_ratio: float,
        max_document_length: int,
    ) -> str | None: ...


class AirtableDocumentRecord(DocumentRecord):
    record_id: str
    quick_ref: str = Field(validation_alias="QuickRef")
    url: str | None = Field(default=None, validation_alias="URL")
    split: TestTrainSplit = Field(validation_alias="Split")

    async def _get_pdf(
        self,
        *,
        cache_dir: Path,
        client: httpx.AsyncClient,
    ) -> Path | None:
        if self.url is None:
            logger.warning(f"Paper {self.quick_ref} is missing a URL")
            _record_failure(
                cache_dir=cache_dir,
                quick_ref=self.quick_ref,
                url=None,
                reason="record has no URL",
            )
            return None
        return await download_pdf(
            url=self.url,
            cache_dir=cache_dir,
            quick_ref=self.quick_ref,
            client=client,
        )

    @override
    async def get_abstract(
        self,
        *,
        cache_dir: Path,
        client: httpx.AsyncClient,
    ) -> str | None:
        pdf_path = await self._get_pdf(cache_dir=cache_dir, client=client)
        if pdf_path is None:
            return None
        return convert_to_markdown(pdf_path, pages=[0])

    @override
    async def get_full_text(
        self,
        *,
        cache_dir: Path,
        client: httpx.AsyncClient,
        max_truncation_ratio: float,
        max_document_length: int,
    ) -> str | None:
        pdf_path = await self._get_pdf(cache_dir=cache_dir, client=client)
        if pdf_path is None:
            return None
        try:
            return _load_full_text(
                pdf_path,
                max_truncation_ratio=max_truncation_ratio,
                max_document_length=max_document_length,
            )
        except RuntimeError as error:
            logger.warning(f"Skipping {self.quick_ref}: {error!r}")
            _record_failure(
                cache_dir=cache_dir,
                quick_ref=self.quick_ref,
                url=self.url,
                reason=repr(error),
            )
            return None


async def fetch_records(
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
    if record.split != split:
        return False
    if document_ids is None:
        return True
    return record.quick_ref in document_ids


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
    quick_ref: str,
    client: httpx.AsyncClient,
) -> Path | None:
    cached = cache_dir / f"{quick_ref}.pdf"
    if cached.exists():
        logger.debug(f"Cache hit: {cached}")
        return cached

    fetch_url = url.replace("https://arxiv.org/abs/", "https://arxiv.org/pdf/")
    cache_dir.mkdir(parents=True, exist_ok=True)

    response = await client.get(fetch_url)
    if response.status_code in {403, 404}:
        logger.warning(
            f"Skipping {quick_ref} due to fetch error: {response.status_code}"
        )
        logger.debug(f"Request for {fetch_url} returned response\n{response.text}")
        _record_failure(
            cache_dir=cache_dir,
            quick_ref=quick_ref,
            url=url,
            reason=f"HTTP {response.status_code}",
        )
        return None
    response.raise_for_status()
    content_type = response.headers.get("content-type", "").split(";")[0].strip()
    if content_type != "application/pdf":
        logger.warning(f"Skipping {quick_ref}: expected PDF, got {content_type}")
        _record_failure(
            cache_dir=cache_dir,
            quick_ref=quick_ref,
            url=url,
            reason=f"expected PDF, got {content_type}",
        )
        return None

    cached.write_bytes(response.content)
    _clear_failure(cache_dir=cache_dir, quick_ref=quick_ref)
    logger.info(f"Downloaded {url} -> {cached}")
    return cached


class DownloadFailure(BaseModel):
    quick_ref: str
    url: str | None
    reason: str
    timestamp: datetime


def _failure_path(cache_dir: Path, quick_ref: str) -> Path:
    return cache_dir / f"{quick_ref}.failed.json"


def _record_failure(
    *,
    cache_dir: Path,
    quick_ref: str,
    url: str | None,
    reason: str,
) -> None:
    cache_dir.mkdir(parents=True, exist_ok=True)
    failure = DownloadFailure(
        quick_ref=quick_ref,
        url=url,
        reason=reason,
        timestamp=datetime.now(UTC),
    )
    _failure_path(cache_dir, quick_ref).write_text(failure.model_dump_json(indent=2))


def _clear_failure(*, cache_dir: Path, quick_ref: str) -> None:
    path = _failure_path(cache_dir, quick_ref)
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
