import csv
import re
from pathlib import Path

from pydantic import BaseModel

# Examples:
# "[...] passage contents"
# "passage contents [...]"
_CUT_MARKER = re.compile(r"^\s*\[\.\.\.\]\s*|\s*\[\.\.\.\]\s*$")
_CONTROL_CHARACTERS = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f]")


class Passage(BaseModel):
    passage_id: str
    document_id: str
    offset: int
    text: str


class _PassageRow(BaseModel):
    passage_id: str
    document_record_id: str
    text: str


class _DocumentRow(BaseModel):
    document_record_id: str
    document_id: str


def load_passages(export_dir: Path) -> list[Passage]:
    with (export_dir / "documents.csv").open(encoding="utf-8", newline="") as file:
        documents = [_DocumentRow.model_validate(row) for row in csv.DictReader(file)]
    document_ids = {row.document_record_id: row.document_id for row in documents}
    with (export_dir / "passages.csv").open(encoding="utf-8", newline="") as file:
        rows = [_PassageRow.model_validate(row) for row in csv.DictReader(file)]
    return [
        Passage(
            passage_id=row.passage_id,
            document_id=document_ids[row.document_record_id],
            offset=int(row.passage_id.rsplit("_", 1)[1]),
            text=_clean(row.text),
        )
        for row in rows
    ]


def _clean(text: str) -> str:
    """Remove control characters and the "[...]" marking a cut at either end."""
    return _CUT_MARKER.sub("", _CONTROL_CHARACTERS.sub("", text))
