import csv
from pathlib import Path

from pydantic import BaseModel


class Excerpt(BaseModel):
    excerpt_id: str
    document_id: str
    text: str
    passage_ids: list[str]


class _ExcerptRow(BaseModel):
    match_id: str
    document_id: str
    excerpt: int
    passages: str
    text: str


def excerpt_id(match_id: str, number: int) -> str:
    return f"{match_id}_excerpt{number}"


def load_excerpts(path: Path) -> list[Excerpt]:
    with path.open(encoding="utf-8", newline="") as file:
        rows = [_ExcerptRow.model_validate(row) for row in csv.DictReader(file)]
    return [
        Excerpt(
            excerpt_id=excerpt_id(row.match_id, row.excerpt),
            document_id=row.document_id,
            text=row.text,
            passage_ids=row.passages.split(";"),
        )
        for row in rows
    ]
