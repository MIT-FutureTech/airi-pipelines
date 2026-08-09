import logging
from collections.abc import Collection, Iterable

from pydantic import BaseModel, Field, TypeAdapter

from risk_repository.classify import (
    DocumentRisks,
    Evidence,
    RiskContent,
    RiskNode,
    codable_risks,
)
from toolbox.airtable import AirtableClient, Table

logger = logging.getLogger(__name__)

REJECTED_ORIGIN = "model-added, human-rejected"

_RISK_FIELDS = [
    "ReadableId",
    "QuickRef",
    "Name",
    "Parent",
    "Description",
    "SupportingQuote",
    "AdditionalEvidence",
    "Origin",
]


class _RiskRecord(BaseModel):
    record_id: str
    readable_id: str = Field(validation_alias="ReadableId")
    quick_ref: str = Field(validation_alias="QuickRef")
    name: str = Field(validation_alias="Name")
    parent_ids: list[str] = Field(default_factory=list, validation_alias="Parent")
    description: str = Field("", validation_alias="Description")
    supporting_quote: str = Field("", validation_alias="SupportingQuote")
    additional_evidence: str = Field("", validation_alias="AdditionalEvidence")
    origin: str = Field(validation_alias="Origin")


class _EvidenceUnit(Evidence, frozen=True):
    text: str = ""
    quote: str = ""


_EVIDENCE_ADAPTER = TypeAdapter(list[_EvidenceUnit])


def _parse_evidence(raw: str) -> tuple[Evidence, ...]:
    if not raw.strip():
        return ()
    units = _EVIDENCE_ADAPTER.validate_json(raw)
    return tuple(
        Evidence(text=unit.text, quote=unit.quote)
        for unit in units
        if unit.text or unit.quote
    )


def _to_node(record: _RiskRecord) -> RiskNode:
    return RiskNode(
        node_id=record.record_id,
        parent_id=record.parent_ids[0] if record.parent_ids else None,
        content=RiskContent(
            name=record.name,
            description=record.description,
            supporting_quote=record.supporting_quote,
            additional_evidence=_parse_evidence(record.additional_evidence),
        ),
        included=record.origin != REJECTED_ORIGIN,
    )


def _group_by_paper(records: Iterable[_RiskRecord]) -> list[DocumentRisks]:
    by_paper: dict[str, list[_RiskRecord]] = {}
    for record in records:
        by_paper.setdefault(record.quick_ref, []).append(record)
    documents: list[DocumentRisks] = []
    for quick_ref, paper in sorted(by_paper.items()):
        paper.sort(key=lambda record: record.readable_id)
        documents.append(
            DocumentRisks(
                readable_id=quick_ref,
                risks=tuple(codable_risks(_to_node(record) for record in paper)),
            )
        )
    return documents


async def fetch_paper_risks(
    client: AirtableClient,
    *,
    base_id: str,
    table_name: str,
    quick_refs: Collection[str],
) -> list[DocumentRisks]:
    table = Table(client, base_id=base_id, table_name=table_name)
    records = [
        _RiskRecord.model_validate({"record_id": record.id, **record.fields})
        async for record in table.iterate(fields=_RISK_FIELDS)
    ]
    if quick_refs:
        records = [record for record in records if record.quick_ref in quick_refs]
    documents = _group_by_paper(records)
    codable = sum(len(document.risks) for document in documents)
    logger.info(
        f"Read {len(records)} risks from {len(documents)} papers, {codable} codable"
    )
    return documents
