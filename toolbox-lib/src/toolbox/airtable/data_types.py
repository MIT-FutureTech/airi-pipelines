from collections.abc import Mapping, Sequence
from datetime import datetime
from typing import ClassVar

from pydantic import BaseModel, ConfigDict, Field

type JsonValue = (
    str | int | float | bool | Sequence[JsonValue] | Mapping[str, JsonValue] | None
)
type JsonObject = Mapping[str, JsonValue]


class Record(BaseModel):
    """An Airtable record."""

    model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True)

    id: str
    created_time: datetime = Field(alias="createdTime")
    fields: JsonObject


class RecordList(BaseModel):
    """Paginated list of records returned by the list-records endpoint."""

    records: list[Record]
    offset: str | None = None


class CreateRecord(BaseModel):
    """Input for batch_create: a single record's fields."""

    fields: JsonObject


class UpdateRecord(BaseModel):
    """Input for batch_update: a record ID and the fields to update."""

    id: str
    fields: JsonObject


class DeletedRecord(BaseModel):
    """Result of deleting a record."""

    model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True)

    id: str
    deleted: bool


class DeletedRecordList(BaseModel):
    """Result of a batch-delete request."""

    records: list[DeletedRecord]


class FieldSpec(BaseModel):
    """Specification for creating or ensuring a field exists."""

    type: str
    options: JsonObject | None = None
    description: str | None = None


class FieldSchema(BaseModel):
    """Field metadata from the Airtable Metadata API."""

    model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True)

    id: str
    name: str
    type: str
    description: str | None = None
    options: JsonObject | None = None


class TableSchema(BaseModel):
    """Table metadata from the Airtable Metadata API."""

    model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True)

    id: str
    name: str
    fields: list[FieldSchema]


class TablesResponse(BaseModel):
    """Response from the Metadata API list-tables endpoint."""

    tables: list[TableSchema]
