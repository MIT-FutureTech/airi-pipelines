from pydantic import BaseModel

from org_mitigations.companies import Company
from org_mitigations.prompt import Prompt
from org_mitigations.search.answer import Answer
from org_mitigations.search.context import Context
from toolbox.llm import StructuredResult, TokenUsage


class SearchResult(BaseModel):
    context_id: str
    domain_code: str
    answer: Answer
    model: str
    usage: TokenUsage | None


class Call(BaseModel):
    call_id: str
    company_name: str
    context: Context
    domain_code: str

    def user_prompt(self, prompt: Prompt) -> str:
        return prompt.render_user(
            company=self.company_name,
            context=self.context.text,
            code=self.domain_code,
            match_id=self.call_id,
        )


def plan_calls(
    contexts: list[Context],
    domain_codes: list[str],
    *,
    companies: list[Company],
) -> list[Call]:
    company_names = {company.company_id: company.name for company in companies}
    return [
        Call(
            call_id=f"{context.context_id}__{domain_code}",
            company_name=company_names[context.company_id],
            context=context,
            domain_code=domain_code,
        )
        for context in contexts
        for domain_code in domain_codes
    ]


def make_search_result(call: Call, response: StructuredResult[Answer]) -> SearchResult:
    return SearchResult(
        context_id=call.context.context_id,
        domain_code=call.domain_code,
        answer=response.value,
        model=response.model,
        usage=response.usage,
    )
