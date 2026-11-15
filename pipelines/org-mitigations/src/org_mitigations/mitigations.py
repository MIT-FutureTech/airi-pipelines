from collections.abc import Mapping

from pydantic import BaseModel

from org_mitigations.answer import Strength
from org_mitigations.calls import CallResult
from org_mitigations.context import Context


class FoundQuote(BaseModel):
    excerpt_id: str
    quote: str
    strength: Strength


class FoundMitigation(BaseModel):
    mitigation_id: str
    company_id: str
    code: str
    name: str
    reasoning: str
    quotes: list[FoundQuote]


def mitigations_from_results(
    results: Mapping[str, CallResult],
    contexts: list[Context],
) -> list[FoundMitigation]:
    contexts_by_id = {context.context_id: context for context in contexts}
    mitigations: list[FoundMitigation] = []
    for call_id, result in results.items():
        context = contexts_by_id[result.context_id]
        for number, mitigation in enumerate(result.answer.classifications, start=1):
            mitigations.append(
                FoundMitigation(
                    mitigation_id=f"{call_id}__{number}",
                    company_id=context.company_id,
                    code=result.code,
                    name=mitigation.mitigation,
                    reasoning=mitigation.reasoning,
                    quotes=[
                        FoundQuote(
                            excerpt_id=_cited_excerpt_id(
                                call_id, context, quote.excerpt
                            ),
                            quote=quote.quote,
                            strength=quote.strength,
                        )
                        for quote in mitigation.evidence
                    ],
                )
            )
    return mitigations


def _cited_excerpt_id(call_id: str, context: Context, number: int) -> str:
    if not 1 <= number <= len(context.excerpt_ids):
        raise ValueError(
            f"{call_id} cites excerpt {number}, but its context has"
            + f" {len(context.excerpt_ids)}"
        )
    return context.excerpt_ids[number - 1]
