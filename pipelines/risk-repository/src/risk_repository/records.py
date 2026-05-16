import csv
import logging
from abc import ABCMeta, abstractmethod
from collections.abc import AsyncIterator, Container
from enum import StrEnum
from pathlib import Path
from typing import override

import httpx
from pydantic import BaseModel, Field

from risk_repository.download import download_pdf, record_failure
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
            record_failure(
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
            record_failure(
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
