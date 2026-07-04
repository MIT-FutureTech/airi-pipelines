from collections.abc import AsyncIterator, Container
from enum import StrEnum

from pydantic import BaseModel, Field

from toolbox.airtable import AirtableClient, Attachment, Table


class TestTrainSplit(StrEnum):
    TRAIN = "train"
    TEST = "test"


class DocumentRecord(BaseModel):
    readable_id: str
    title: str | None
    abstract: str | None
    url: str | None
    split: TestTrainSplit | None = None


class ScreeningRecord(DocumentRecord):
    """A record from an Airtable screening table.

    The screened PDF is an attachment on the record rather than a URL, and the
    Airtable record ID doubles as the readable ID.
    """

    record_id: str
    title: str | None
    abstract: str | None = None
    url: str | None = None
    attachments: list[Attachment] = Field(
        default_factory=list, validation_alias="full_text_pdf"
    )

    @property
    def has_pdf(self) -> bool:
        return bool(self.attachments)


async def fetch_screening_records(
    client: AirtableClient,
    *,
    base_id: str,
    table_name: str,
) -> AsyncIterator[ScreeningRecord]:
    table = Table(client, base_id=base_id, table_name=table_name)
    async for record in table.iterate(fields=["title", "abstract", "full_text_pdf"]):
        yield ScreeningRecord.model_validate(
            {"readable_id": record.id, "record_id": record.id, **record.fields}
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
