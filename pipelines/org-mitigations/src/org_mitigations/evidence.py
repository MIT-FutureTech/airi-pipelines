from pydantic import BaseModel

from org_mitigations.excerpts import Excerpt
from org_mitigations.search.answer import Strength
from org_mitigations.search.mitigations import FoundMitigation


class Evidence(BaseModel):
    evidence_id: str
    mitigation_id: str
    document_id: str
    domain_code: str
    mitigation_name: str
    reasoning: str
    quote: str
    strength: Strength
    excerpt_id: str


def evidence_from_mitigations(
    mitigations: list[FoundMitigation],
    excerpts: list[Excerpt],
) -> list[Evidence]:
    document_ids = {excerpt.excerpt_id: excerpt.document_id for excerpt in excerpts}
    return [
        Evidence(
            evidence_id=f"{mitigation.mitigation_id}.{number}",
            mitigation_id=mitigation.mitigation_id,
            document_id=document_ids[quote.excerpt_id],
            domain_code=mitigation.domain_code,
            mitigation_name=mitigation.name,
            reasoning=mitigation.reasoning,
            quote=quote.quote,
            strength=quote.strength,
            excerpt_id=quote.excerpt_id,
        )
        for mitigation in mitigations
        for number, quote in enumerate(mitigation.quotes, start=1)
    ]
