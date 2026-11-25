from org_mitigations.companies import Company
from org_mitigations.prompt import Prompt
from org_mitigations.search.calls import plan_calls
from org_mitigations.search.context import Context

PROMPT = Prompt(
    system="Find mitigations.",
    user_template="$company|$code|$match_id|$context",
)
COMPANIES = [
    Company(company_id="recA", name="Example Bank", sector="Finance"),
    Company(company_id="recB", name="Example Retail", sector="Retail"),
]
CONTEXTS = [
    Context(
        context_id="Example_Bank",
        company_id="recA",
        text="<document>bank</document>",
        excerpt_ids=["Example_Bank_001_excerpt1"],
    ),
    Context(
        context_id="Example_Retail",
        company_id="recB",
        text="<document>retail</document>",
        excerpt_ids=["Example_Retail_001_excerpt1"],
    ),
]


class TestPlanCalls:
    def test_makes_a_call_for_each_context_and_code(self) -> None:
        calls = plan_calls(CONTEXTS, ["1.1", "2.1"], companies=COMPANIES)

        assert [(call.call_id, call.company_name) for call in calls] == [
            ("Example_Bank__1.1", "Example Bank"),
            ("Example_Bank__2.1", "Example Bank"),
            ("Example_Retail__1.1", "Example Retail"),
            ("Example_Retail__2.1", "Example Retail"),
        ]

    def test_fills_in_the_user_prompt_for_a_call(self) -> None:
        [call] = plan_calls(CONTEXTS[:1], ["2.1"], companies=COMPANIES)

        assert call.user_prompt(PROMPT) == (
            "Example Bank|2.1|Example_Bank__2.1|<document>bank</document>"
        )
