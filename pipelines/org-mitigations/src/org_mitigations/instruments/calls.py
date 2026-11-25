from collections import defaultdict

from pydantic import BaseModel

from org_mitigations.instrument_taxonomy import Modality
from org_mitigations.instruments.answer import Answer, invalid_code_reason
from org_mitigations.prompt import Prompt
from org_mitigations.search.mitigations import FoundMitigation
from toolbox.llm import StructuredResult, TokenUsage, ToolboxLLMInvalidResponseError


class InstrumentsResult(BaseModel):
    mitigation_id: str
    answer: Answer
    model: str
    usage: TokenUsage | None


class Call(BaseModel):
    mitigation: FoundMitigation
    context_mitigations: list[FoundMitigation]

    @property
    def call_id(self) -> str:
        return self.mitigation.mitigation_id

    def user_prompt(self, prompt: Prompt) -> str:
        return prompt.render_user(
            context_mitigations="\n".join(
                self._listing(other) for other in self.context_mitigations
            ),
            name=self.mitigation.name,
            description=self.mitigation.reasoning,
            evidence="\n".join(
                f"<quote>{quote.quote.strip()}</quote>"
                for quote in self.mitigation.quotes
            ),
        )

    def _listing(self, other: FoundMitigation) -> str:
        line = f"- {other.name}: {other.reasoning}"
        if other.mitigation_id == self.mitigation.mitigation_id:
            line += " <-- THIS MITIGATION (classify this one)"
        return line


def plan_calls(mitigations: list[FoundMitigation]) -> list[Call]:
    by_context: defaultdict[str, list[FoundMitigation]] = defaultdict(list)
    for mitigation in mitigations:
        by_context[mitigation.context_id].append(mitigation)
    return [
        Call(
            mitigation=mitigation,
            context_mitigations=by_context[mitigation.context_id],
        )
        for mitigation in mitigations
    ]


def make_instruments_result(
    call: Call,
    response: StructuredResult[Answer],
    *,
    modalities: list[Modality],
) -> InstrumentsResult:
    reason = invalid_code_reason(response.value, modalities)
    if reason:
        raise ToolboxLLMInvalidResponseError(reason)
    return InstrumentsResult(
        mitigation_id=call.call_id,
        answer=response.value,
        model=response.model,
        usage=response.usage,
    )
