from collections.abc import Mapping

from pydantic import BaseModel, Field, field_serializer

from org_mitigations.evidence import Evidence
from org_mitigations.excerpts import Excerpt
from org_mitigations.locate import Span, locate_quote
from org_mitigations.passages import Passage
from org_mitigations.search.answer import Strength
from org_mitigations.sync.schema import FieldType

_STRENGTH_LABELS = {
    Strength.DESCRIBED: "Described",
    Strength.STATED: "Stated",
    Strength.REFERENCE: "Reference",
}


class QuoteRecord(BaseModel):
    evidence_id: str = Field(serialization_alias="ID")
    mitigation_record_id: str = Field(serialization_alias="Mitigation")
    document_record_id: str = Field(serialization_alias="Document")
    passage_record_ids: list[str] = Field(serialization_alias="Passages")
    quote: str = Field(serialization_alias="Quote")
    strength: Strength = Field(serialization_alias="Strength")

    @field_serializer("mitigation_record_id", "document_record_id")
    def _serialize_link(self, record_id: str) -> list[str]:
        return [record_id]

    @field_serializer("strength")
    def _serialize_strength(self, strength: Strength) -> str:
        return _STRENGTH_LABELS[strength]


QUOTE_FIELD_TYPES = {
    "ID": FieldType.SINGLE_LINE_TEXT,
    "Mitigation": FieldType.LINKS,
    "Document": FieldType.LINKS,
    "Passages": FieldType.LINKS,
    "Quote": FieldType.LONG_TEXT,
    "Strength": FieldType.SINGLE_SELECT,
}


def quote_records(
    *,
    evidence: list[Evidence],
    excerpts: list[Excerpt],
    passages: list[Passage],
    mitigation_record_ids: Mapping[str, str],
    document_record_ids: Mapping[str, str],
    passage_record_ids: Mapping[str, str],
) -> list[QuoteRecord]:
    excerpts_by_id = {excerpt.excerpt_id: excerpt for excerpt in excerpts}
    passages_by_id = {passage.passage_id: passage for passage in passages}
    return [
        QuoteRecord(
            evidence_id=item.evidence_id,
            mitigation_record_id=mitigation_record_ids[item.mitigation_id],
            document_record_id=document_record_ids[item.document_id],
            passage_record_ids=[
                passage_record_ids[passage_id]
                for passage_id in _quoted_passage_ids(
                    item.quote, excerpts_by_id[item.excerpt_id], passages_by_id
                )
            ],
            quote=item.quote,
            strength=item.strength,
        )
        for item in evidence
    ]


def _quoted_passage_ids(
    quote: str, excerpt: Excerpt, passages: Mapping[str, Passage]
) -> list[str]:
    """List the passages a quote overlaps, or all of them if it can't be found."""
    location = locate_quote(quote, excerpt.text)
    if location is None:
        return excerpt.passage_ids
    return [
        passage_id
        for passage_id, span in _passage_spans(excerpt, passages)
        if span.start < location.end and location.start < span.end
    ]


def _passage_spans(
    excerpt: Excerpt, passages: Mapping[str, Passage]
) -> list[tuple[str, Span]]:
    spans: list[tuple[str, Span]] = []
    search_from = 0
    for passage_id in excerpt.passage_ids:
        text = passages[passage_id].text
        start = excerpt.text.find(text, search_from)
        if start == -1:
            raise ValueError(
                f"Passage {passage_id} isn't in excerpt {excerpt.excerpt_id}"
            )
        spans.append((passage_id, Span(start=start, end=start + len(text))))
        search_from = start
    return spans
