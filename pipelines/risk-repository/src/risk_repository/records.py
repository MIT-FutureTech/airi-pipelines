from collections.abc import AsyncIterator, Container
from enum import StrEnum

from pydantic import BaseModel, Field

from toolbox.airtable import AirtableClient, Attachment, Table


class DocumentSource(StrEnum):
    SCREENING_TABLE = "screening_table"
    TRAINING_SET = "training_set"


class DocumentRecord(BaseModel):
    readable_id: str
    title: str | None
    abstract: str | None
    url: str | None


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
    view: str | None = None,
) -> AsyncIterator[ScreeningRecord]:
    table = Table(client, base_id=base_id, table_name=table_name)
    async for record in table.iterate(
        fields=["title", "abstract", "full_text_pdf"], view=view
    ):
        yield ScreeningRecord.model_validate(
            {"readable_id": record.id, "record_id": record.id, **record.fields}
        )


async def fetch_training_set_records(
    client: AirtableClient,
    *,
    base_id: str,
    table_name: str,
    view: str | None = None,
) -> AsyncIterator[DocumentRecord]:
    """Yield documents from a curated table keyed by QuickRef.

    Unlike screening records, full text is fetched from each record's PDFURL (or URL
    as a fallback) rather than from an attached PDF.
    """
    table = Table(client, base_id=base_id, table_name=table_name)
    fields = ["QuickRef", "DocTitle", "Abstract", "URL", "PDFURL"]
    async for record in table.iterate(fields=fields, view=view):
        values = record.fields
        yield DocumentRecord.model_validate(
            {
                "readable_id": values["QuickRef"],
                "title": values.get("DocTitle"),
                "abstract": values.get("Abstract"),
                "url": values.get("PDFURL") or values.get("URL"),
            }
        )


def include_record(
    record: DocumentRecord,
    document_ids: Container[str] | None,
) -> bool:
    if document_ids is None:
        return True
    return record.readable_id in document_ids
