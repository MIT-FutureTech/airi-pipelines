from pydantic import BaseModel

from org_mitigations.companies import Company
from org_mitigations.prompt import Prompt
from org_mitigations.search.mitigations import FoundMitigation


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
