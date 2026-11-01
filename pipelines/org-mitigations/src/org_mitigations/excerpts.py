import csv
from collections import defaultdict
from pathlib import Path

from pydantic import BaseModel

from org_mitigations.passages import Passage

_MIN_OVERLAP = 80


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


def merge_passages(passages: list[Passage]) -> list[Excerpt]:
    by_document: defaultdict[str, list[Passage]] = defaultdict(list)
    for passage in passages:
        by_document[passage.document_id].append(passage)
    excerpts: list[Excerpt] = []
    for document_id in sorted(by_document):
        excerpts.extend(_merge_document(document_id, by_document[document_id]))
    return excerpts


def _merge_document(document_id: str, passages: list[Passage]) -> list[Excerpt]:
    texts: list[str] = []
    members: list[list[Passage]] = []
    for passage in sorted(passages, key=lambda passage: passage.offset):
        if texts:
            if passage.text in texts[-1]:
                members[-1].append(passage)
                continue
            start = _overlap_start(texts[-1], passage.text)
            if start is not None:
                texts[-1] = texts[-1][:start] + passage.text
                members[-1].append(passage)
                continue
        texts.append(passage.text)
        members.append([passage])

    if any(
        passage.text not in text
        for text, run in zip(texts, members, strict=True)
        for passage in run
    ):
        raise ValueError(f"A passage of {document_id} was lost while merging")
    return [
        Excerpt(
            excerpt_id=excerpt_id(document_id, number),
            document_id=document_id,
            text=text,
            passage_ids=[passage.passage_id for passage in run],
        )
        for number, (text, run) in enumerate(zip(texts, members, strict=True), start=1)
    ]


def _overlap_start(text: str, following: str) -> int | None:
    probe = following[:_MIN_OVERLAP]
    start = text.find(probe)
    while start >= 0:
        if following.startswith(text[start:]):
            return start
        start = text.find(probe, start + 1)
    return None
