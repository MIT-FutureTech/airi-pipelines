import csv
import datetime
from enum import StrEnum
from pathlib import Path
from typing import Annotated

from pydantic import BaseModel, BeforeValidator


def _none_if_empty(value: object) -> object:
    return value or None


class DatePrecision(StrEnum):
    DAY = "day"
    MONTH = "month"
    YEAR = "year"


class Document(BaseModel):
    document_id: str
    company_id: str
    title: str
    doc_type: str
    date: Annotated[datetime.date | None, BeforeValidator(_none_if_empty)]
    date_precision: Annotated[DatePrecision | None, BeforeValidator(_none_if_empty)]
    link: str


class _DocumentRecordRow(BaseModel):
    document_record_id: str
    document_id: str


def load_documents(export_dir: Path) -> list[Document]:
    with (export_dir / "documents.csv").open(encoding="utf-8", newline="") as file:
        return [Document.model_validate(row) for row in csv.DictReader(file)]


def load_document_record_ids(export_dir: Path) -> dict[str, str]:
    """Map each document ID to the ID of its record in Airtable."""
    with (export_dir / "documents.csv").open(encoding="utf-8", newline="") as file:
        rows = [_DocumentRecordRow.model_validate(row) for row in csv.DictReader(file)]
    return {row.document_id: row.document_record_id for row in rows}
