from pydantic import BaseModel

from org_mitigations.companies import Company
from org_mitigations.practice_list import Practice
from org_mitigations.practices.answer import Answer, unlisted_names
from org_mitigations.prompt import Prompt
from org_mitigations.search.mitigations import FoundMitigation
from toolbox.llm import StructuredResult, TokenUsage, ToolboxLLMInvalidResponseError


class PracticesResult(BaseModel):
    mitigation_id: str
    answer: Answer
    model: str
    usage: TokenUsage | None


class Call(BaseModel):
    call_id: str
    company_name: str
    quotes: list[str]

    def user_prompt(self, prompt: Prompt) -> str:
        return prompt.render_user(
            company=self.company_name,
            quotes="\n".join(
                f'<quote id="{number}">{quote.strip()}</quote>'
                for number, quote in enumerate(self.quotes, start=1)
            ),
            match_id=self.call_id,
        )


def plan_calls(
    mitigations: list[FoundMitigation],
    *,
    companies: list[Company],
) -> list[Call]:
    company_names = {company.company_id: company.name for company in companies}
    return [
        Call(
            call_id=mitigation.mitigation_id,
            company_name=company_names[mitigation.company_id],
            quotes=[quote.quote for quote in mitigation.quotes],
        )
        for mitigation in mitigations
    ]


def make_practices_result(
    call: Call,
    response: StructuredResult[Answer],
    *,
    practices: list[Practice],
) -> PracticesResult:
    unlisted = unlisted_names(response.value, practices)
    if unlisted:
        raise ToolboxLLMInvalidResponseError(
            f"Names not in the practice list: {unlisted}"
        )
    return PracticesResult(
        mitigation_id=call.call_id,
        answer=response.value,
        model=response.model,
        usage=response.usage,
    )
