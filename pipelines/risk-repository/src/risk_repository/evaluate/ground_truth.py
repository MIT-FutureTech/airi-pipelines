import logging
from enum import StrEnum

from pydantic import BaseModel, Field, TypeAdapter, ValidationError, field_validator

from risk_repository.screen import Decision
from toolbox.airtable import AirtableClient, Table

logger = logging.getLogger(__name__)

_EVIDENCE_ADAPTER = TypeAdapter(list[str])


class CategoryLevel(StrEnum):
    CATEGORY = "category"
    SUBCATEGORY = "subcategory"


class _CausalFactor(BaseModel):
    record_id: str
    label: str = Field(validation_alias="Causal Factor")


class _Subdomain(BaseModel):
    record_id: str
    code: str = Field(validation_alias="Risk Subdomain Code")


class _UnresolvedRisk(BaseModel):
    """Risk record with linked-record IDs not yet resolved to values."""

    ev_id: str = Field(validation_alias="Ev_ID")
    document_ids: list[str] = Field(validation_alias="Document_ID")
    category: str = Field(validation_alias="Risk category")
    subcategory: str | None = Field(None, validation_alias="Risk Subcategory")
    description: str | None = Field(None, validation_alias="Description_Clean")
    quote: str | None = Field(None, validation_alias="Description")
    category_level: str | None = Field(None, validation_alias="Category level")
    additional_evidence_raw: str | None = Field(
        None, validation_alias="Additional evidence"
    )
    page: int | None = Field(None, validation_alias="Description_page")
    entity_ids: list[str] = Field(
        default_factory=list, validation_alias="CausalTax_Entity"
    )
    intent_ids: list[str] = Field(
        default_factory=list, validation_alias="CausalTax_Intent"
    )
    timing_ids: list[str] = Field(
        default_factory=list, validation_alias="CausalTax_Timing"
    )
    subdomain_ids: list[str] = Field(
        default_factory=list, validation_alias="Subdomain Category"
    )


class GroundTruthDocument(BaseModel):
    record_id: str
    readable_id: str = Field(validation_alias="QuickRef")
    screening_result: Decision | None = Field(
        default=None,
        validation_alias="ScreeningResult",
    )

    @field_validator("screening_result", mode="before")
    @classmethod
    def normalize_case(cls, value: str | None) -> str | None:
        if isinstance(value, str):
            return value.lower()
        return value


class GroundTruthRisk(BaseModel):
    ev_id: str
    document_readable_id: str
    category_level: CategoryLevel | None
    category: str
    subcategory: str | None
    description: str
    quote: str | None
    additional_evidence: list[str]
    page: int | None
    entity: str | None
    intent: str | None
    timing: str | None
    subdomain_code: str | None

    @property
    def level(self) -> CategoryLevel:
        if self.category_level is not None:
            return self.category_level
        return CategoryLevel.SUBCATEGORY if self.subcategory else CategoryLevel.CATEGORY


class GroundTruth(BaseModel):
    documents: list[GroundTruthDocument]
    risks: list[GroundTruthRisk]

    def risks_by_document(self) -> dict[str, list[GroundTruthRisk]]:
        by_doc: dict[str, list[GroundTruthRisk]] = {}
        for risk in self.risks:
            by_doc.setdefault(risk.document_readable_id, []).append(risk)
        return by_doc


async def fetch_ground_truth(
    client: AirtableClient,
    *,
    base_id: str,
    documents_table_name: str,
) -> GroundTruth:
    documents = await fetch_ground_truth_documents(
        client=client,
        base_id=base_id,
        documents_table_name=documents_table_name,
    )
    doc_id_to_readable_id = await _fetch_id_map(client, base_id)
    causal_map = await _fetch_causal_map(client, base_id)
    subdomain_map = await _fetch_subdomain_map(client, base_id)
    risks = await _fetch_risks(
        client,
        base_id=base_id,
        doc_id_to_readable_id=doc_id_to_readable_id,
        causal_map=causal_map,
        subdomain_map=subdomain_map,
    )
    logger.info(f"Loaded ground truth: {len(documents)} documents, {len(risks)} risks")
    return GroundTruth(documents=documents, risks=risks)


async def _fetch_id_map(
    client: AirtableClient,
    base_id: str,
) -> dict[str, str]:
    """Map record IDs in the production Documents table to readable ones.

    The AI Risk Database table links to Documents via record IDs, so this
    mapping must always come from the production table regardless of which
    table is used for ground truth documents.
    """

    class _RecordModel(BaseModel):
        readable_id: str = Field(validation_alias="QuickRef")

    table = Table(client, base_id=base_id, table_name="Documents")
    result: dict[str, str] = {}
    async for raw_record in table.iterate(fields=["QuickRef"]):
        record = _RecordModel.model_validate(raw_record.fields)
        result[raw_record.id] = record.readable_id
    return result


async def fetch_ground_truth_documents(
    client: AirtableClient,
    *,
    base_id: str,
    documents_table_name: str,
) -> list[GroundTruthDocument]:
    table = Table(client, base_id=base_id, table_name=documents_table_name)
    documents: list[GroundTruthDocument] = []
    async for record in table.iterate(fields=["QuickRef", "ScreeningResult"]):
        doc = GroundTruthDocument.model_validate(
            {"record_id": record.id, **record.fields}
        )
        documents.append(doc)
    return documents


class _ScreeningReview(BaseModel):
    record_id: str
    human_include_1: str | None = None
    human_include_2: str | None = None


def _review_decision(value: str | None) -> Decision | None:
    match value:
        case "Include":
            return Decision.INCLUDE
        case "Exclude":
            return Decision.EXCLUDE
        case _:
            return None


def _ground_truth_from_reviews(review: _ScreeningReview) -> Decision | None:
    """Combine two human reviewers into a ground-truth decision using OR.

    Includes when at least one reviewer included; excludes when at least one
    reviewer decided and none included; None when neither reviewer decided.
    """
    decisions = [
        d
        for d in (
            _review_decision(review.human_include_1),
            _review_decision(review.human_include_2),
        )
        if d is not None
    ]
    if not decisions:
        return None
    if Decision.INCLUDE in decisions:
        return Decision.INCLUDE
    return Decision.EXCLUDE


async def fetch_screening_ground_truth(
    client: AirtableClient,
    *,
    base_id: str,
    table_name: str,
) -> dict[str, Decision | None]:
    """Map each screening-table record ID to its human ground-truth decision."""
    table = Table(client, base_id=base_id, table_name=table_name)
    ground_truth: dict[str, Decision | None] = {}
    async for record in table.iterate(fields=["human_include_1", "human_include_2"]):
        review = _ScreeningReview.model_validate(
            {"record_id": record.id, **record.fields}
        )
        ground_truth[record.id] = _ground_truth_from_reviews(review)
    return ground_truth


async def _fetch_causal_map(client: AirtableClient, base_id: str) -> dict[str, str]:
    """Map Causal Taxonomy record IDs to their label (e.g. "Entity: Human")."""
    table = Table(client, base_id=base_id, table_name="Causal Taxonomy")
    result: dict[str, str] = {}
    async for record in table.iterate(fields=["Causal Factor"]):
        raw = _CausalFactor.model_validate({"record_id": record.id, **record.fields})
        result[raw.record_id] = raw.label
    return result


async def _fetch_subdomain_map(client: AirtableClient, base_id: str) -> dict[str, str]:
    """Map Domain Taxonomy (Subdomains) record IDs to their code (e.g. "3.1")."""
    table = Table(client, base_id=base_id, table_name="Domain Taxonomy (Subdomains)")
    result: dict[str, str] = {}
    async for record in table.iterate(fields=["Risk Subdomain Code"]):
        raw = _Subdomain.model_validate({"record_id": record.id, **record.fields})
        result[raw.record_id] = raw.code
    return result


def _parse_causal_label(label: str) -> str | None:
    """Parse "Entity: Human" -> "Human", "Not coded" -> None."""
    if label == "Not coded":
        return None
    if ": " in label:
        return label.split(": ", 1)[1]
    return label


def _parse_subdomain_code(code: str) -> str | None:
    if code == "X.1":
        return None
    return code


def _resolve_causal(ids: list[str], causal_map: dict[str, str]) -> str | None:
    if not ids:
        return None
    return _parse_causal_label(causal_map[ids[0]])


def _resolve_subdomain(ids: list[str], subdomain_map: dict[str, str]) -> str | None:
    if not ids:
        return None
    return _parse_subdomain_code(subdomain_map[ids[0]])


def _parse_category_level(value: str | None) -> CategoryLevel | None:
    match value:
        case "Risk Category":
            return CategoryLevel.CATEGORY
        case "Risk Sub-Category":
            return CategoryLevel.SUBCATEGORY
        case _:
            return None


def _parse_additional_evidence(value: str | None) -> list[str]:
    if not value:
        return []
    try:
        return _EVIDENCE_ADAPTER.validate_json(value)
    except ValidationError:
        logger.warning(f"Could not parse Additional evidence: {value[:80]!r}")
        return [value]


async def _fetch_risks(
    client: AirtableClient,
    *,
    base_id: str,
    doc_id_to_readable_id: dict[str, str],
    causal_map: dict[str, str],
    subdomain_map: dict[str, str],
) -> list[GroundTruthRisk]:
    table = Table(client, base_id=base_id, table_name="AI Risk Database")
    risks: list[GroundTruthRisk] = []
    async for record in table.iterate():
        raw = _UnresolvedRisk.model_validate(record.fields)
        readable_id = doc_id_to_readable_id[raw.document_ids[0]]
        risks.append(
            GroundTruthRisk(
                ev_id=raw.ev_id,
                document_readable_id=readable_id,
                category_level=_parse_category_level(raw.category_level),
                category=raw.category,
                subcategory=raw.subcategory,
                description=raw.description or "",
                quote=raw.quote,
                additional_evidence=_parse_additional_evidence(
                    raw.additional_evidence_raw
                ),
                page=raw.page,
                entity=_resolve_causal(raw.entity_ids, causal_map),
                intent=_resolve_causal(raw.intent_ids, causal_map),
                timing=_resolve_causal(raw.timing_ids, causal_map),
                subdomain_code=_resolve_subdomain(raw.subdomain_ids, subdomain_map),
            )
        )

    return risks
