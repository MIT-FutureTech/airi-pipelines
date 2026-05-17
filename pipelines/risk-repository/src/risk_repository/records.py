import csv
from collections.abc import AsyncIterator, Container
from enum import StrEnum
from pathlib import Path

from pydantic import BaseModel, Field

from toolbox.airtable import AirtableClient, Table


class TestTrainSplit(StrEnum):
    TRAIN = "train"
    TEST = "test"


class DocumentRecord(BaseModel):
    readable_id: str
    title: str | None
    abstract: str | None
    url: str | None
    split: TestTrainSplit | None = None


class AirtableDocumentRecord(DocumentRecord):
    record_id: str
    readable_id: str = Field(validation_alias="QuickRef")
    title: str | None = Field(validation_alias="DocTitle")
    abstract: str | None = Field(default=None, validation_alias="Abstract")
    url: str | None = Field(default=None, validation_alias="URL")
    split: TestTrainSplit | None = Field(default=None, validation_alias="Split")


class CsvDocumentRecord(DocumentRecord):
    doi: str | None = None
    url: str | None = Field(default=None, alias="link")
    author_keywords: str | None = None


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
