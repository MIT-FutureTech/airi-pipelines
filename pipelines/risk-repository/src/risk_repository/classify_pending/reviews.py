import logging
from collections.abc import Iterable, Mapping, Sequence
from enum import StrEnum

from pydantic import BaseModel, Field

from risk_repository.classify import ClassifiedRisk, DocumentRisks
from toolbox.airtable import AirtableClient, JsonObject, Table

logger = logging.getLogger(__name__)

PIPELINE_REVIEWER_PREFIX = "pipeline:"
PIPELINE_MODE = "blind"


class ReviewField(StrEnum):
    VALIDITY = "validity"
    ENTITY = "entity"
    INTENT = "intent"
    TIMING = "timing"
    SUBDOMAIN = "subdomain"


AXIS_FIELDS = frozenset(
    {
        ReviewField.ENTITY,
        ReviewField.INTENT,
        ReviewField.TIMING,
        ReviewField.SUBDOMAIN,
    }
)

_PIPELINE_FORMULA = (
    f'LEFT({{Reviewer}}, {len(PIPELINE_REVIEWER_PREFIX)})="{PIPELINE_REVIEWER_PREFIX}"'
)


class _ReviewRecord(BaseModel):
    record_id: str
    risk_ids: list[str] = Field(default_factory=list, validation_alias="Risk")
    field: ReviewField = Field(validation_alias="Field")


class PipelineCoding(BaseModel, frozen=True):
    """The pipeline's existing review rows for one risk."""

    review_ids: tuple[str, ...]
    coded_fields: frozenset[ReviewField]

    @property
    def is_complete(self) -> bool:
        return self.coded_fields >= AXIS_FIELDS


async def fetch_pipeline_codings(
    client: AirtableClient,
    *,
    base_id: str,
    table_name: str,
) -> dict[str, PipelineCoding]:
    table = Table(client, base_id=base_id, table_name=table_name)
    by_risk: dict[str, list[_ReviewRecord]] = {}
    async for record in table.iterate(
        formula=_PIPELINE_FORMULA,
        fields=["Risk", "Field"],
    ):
        review = _ReviewRecord.model_validate({"record_id": record.id, **record.fields})
        if not review.risk_ids:
            logger.warning(f"Skipping review {review.record_id}: not linked to a risk")
            continue
        by_risk.setdefault(review.risk_ids[0], []).append(review)
    codings = {
        risk_id: PipelineCoding(
            review_ids=tuple(review.record_id for review in reviews),
            coded_fields=frozenset(review.field for review in reviews),
        )
        for risk_id, reviews in by_risk.items()
    }
    logger.info(f"Read pipeline classifications for {len(codings)} risks")
    return codings


def pending_risks(
    documents: Iterable[DocumentRisks],
    codings: Mapping[str, PipelineCoding],
) -> list[DocumentRisks]:
    """Narrow each paper to the risks missing pipeline classifications"""
    pending: list[DocumentRisks] = []
    for document in documents:
        risks = tuple(
            risk
            for risk in document.risks
            if risk.risk_id not in codings or not codings[risk.risk_id].is_complete
        )
        if risks:
            pending.append(DocumentRisks(readable_id=document.readable_id, risks=risks))
    total = sum(len(document.risks) for document in pending)
    logger.info(f"{total} risks in {len(pending)} papers need classifying")
    return pending


class _AxisCoding(BaseModel, frozen=True):
    field: ReviewField
    value: str
    comment: str


def _axis_codings(classified: ClassifiedRisk) -> tuple[_AxisCoding, ...]:
    """One coding per axis, each carrying the reasoning that produced it.

    The causal reasoning covers three axes at once, so it repeats across them.
    """
    causal = classified.causal
    domain = classified.domain
    return (
        _AxisCoding(
            field=ReviewField.ENTITY,
            value=causal.entity.value,
            comment=causal.reasoning,
        ),
        _AxisCoding(
            field=ReviewField.INTENT,
            value=causal.intent.value,
            comment=causal.reasoning,
        ),
        _AxisCoding(
            field=ReviewField.TIMING,
            value=causal.timing.value,
            comment=causal.reasoning,
        ),
        _AxisCoding(
            field=ReviewField.SUBDOMAIN,
            value=domain.subdomain.value,
            comment=domain.reasoning,
        ),
    )


async def replace_pipeline_codings(
    client: AirtableClient,
    *,
    base_id: str,
    table_name: str,
    reviewer: str,
    classified: Sequence[ClassifiedRisk],
    codings: Mapping[str, PipelineCoding],
) -> None:
    table = Table(client, base_id=base_id, table_name=table_name)
    stale = [
        review_id
        for risk in classified
        if risk.risk_id in codings
        for review_id in codings[risk.risk_id].review_ids
    ]
    if stale:
        await table.batch_delete(stale)
    rows: list[JsonObject] = [
        {
            "Risk": [risk.risk_id],
            "Reviewer": reviewer,
            "Field": coding.field.value,
            "Value": coding.value,
            "Mode": PIPELINE_MODE,
            "Comment": coding.comment,
        }
        for risk in classified
        for coding in _axis_codings(risk)
    ]
    await table.batch_create(rows)
    logger.info(
        f"Wrote {len(rows)} rows for {len(classified)} risks, {len(stale)} stale rows deleted"
    )
