from collections.abc import Mapping, Sequence
from datetime import datetime

from pydantic import BaseModel, Field

type JsonValue = (
    str | int | float | bool | Sequence[JsonValue] | Mapping[str, JsonValue] | None
)
type JsonObject = Mapping[str, JsonValue]


class Attachment(BaseModel, frozen=True):
    """A file stored in an Airtable attachment field."""

    id: str
    # Short-lived download URL
    url: str
    filename: str
    size: int | None = None
    type: str | None = None


class Record(BaseModel, frozen=True):
    """An Airtable record."""

    id: str
    created_time: datetime = Field(alias="createdTime")
    fields: JsonObject

    def attachments(self, field: str) -> list[Attachment]:
        value = self.fields[field]
        if not isinstance(value, list):
            raise TypeError(f"Field {field!r} is not an attachment field")
        return [Attachment.model_validate(item) for item in value]


class RecordList(BaseModel, frozen=True):
    """Paginated list of records returned by the list-records endpoint."""

    records: list[Record]
    offset: str | None = None


class CreateRecord(BaseModel, frozen=True):
    """Input for batch_create: a single record's fields."""

    fields: JsonObject


class UpdateRecord(BaseModel, frozen=True):
    """Input for batch_update: a record ID and the fields to update."""

    id: str
    fields: JsonObject


class DeletedRecord(BaseModel, frozen=True):
    """Result of deleting a record."""

    id: str
    deleted: bool


class DeletedRecordList(BaseModel, frozen=True):
    """Result of a batch-delete request."""

    records: list[DeletedRecord]


class FieldSpec(BaseModel, frozen=True):
    """Specification for creating or ensuring a field exists."""

    type: str
    options: JsonObject | None = None
    description: str | None = None


class FieldSchema(BaseModel, frozen=True):
    """Field metadata from the Airtable Metadata API."""

    id: str
    name: str
    type: str
    description: str | None = None
    options: JsonObject | None = None


class TableSchema(BaseModel, frozen=True):
    """Table metadata from the Airtable Metadata API."""

    id: str
    name: str
    fields: list[FieldSchema]


class TablesResponse(BaseModel, frozen=True):
    """Response from the Metadata API list-tables endpoint."""

    tables: list[TableSchema]
