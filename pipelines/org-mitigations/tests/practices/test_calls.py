import pytest

from org_mitigations.companies import Company
from org_mitigations.practice_list import Practice
from org_mitigations.practices.answer import Answer, TaggedPractice
from org_mitigations.practices.calls import (
    Call,
    PracticesResult,
    make_practices_result,
    plan_calls,
)
from org_mitigations.prompt import Prompt
from org_mitigations.search.answer import Strength
from org_mitigations.search.mitigations import FoundMitigation, FoundQuote
from toolbox.llm import StructuredResult, ToolboxLLMInvalidResponseError
from toolbox.llm.stub import STUB_MODEL, STUB_USAGE

PROMPT = Prompt(
    system="Tag practices.",
    user_template="$company|$match_id\n$quotes",
)
COMPANIES = [
    Company(company_id="recA", name="Example Bank", sector="Finance"),
    Company(company_id="recB", name="Example Retail", sector="Retail"),
]
PRACTICES = [
    Practice(
        name="Formal AI oversight and accountability",
        definition="Formal AI oversight is a governance arrangement.",
        counts=["Board or board-committee oversight of AI risk."],
        does_not_count=["One-off briefings."],
        subtypes=["Board of directors oversight"],
    ),
]
CALL = Call(
    call_id="Example_Bank__2.2__1",
    company_name="Example Bank",
    quotes=["Our board oversees AI."],
)


def _mitigation(mitigation_id: str, company_id: str, *quotes: str) -> FoundMitigation:
    return FoundMitigation(
        mitigation_id=mitigation_id,
        company_id=company_id,
        domain_code="2.2",
        name="Board oversight of AI",
        reasoning="Board-level accountability for AI.",
        quotes=[
            FoundQuote(
                excerpt_id=f"{mitigation_id}_excerpt1",
                quote=quote,
                strength=Strength.STATED,
            )
            for quote in quotes
        ],
    )


class TestPlanCalls:
    def test_makes_a_call_for_each_mitigation(self) -> None:
        calls = plan_calls(
            [
                _mitigation("Example_Bank__2.2__1", "recA", "Our board oversees AI."),
                _mitigation("Example_Retail__2.2__1", "recB", "Our CTO owns AI."),
            ],
            companies=COMPANIES,
        )

        assert [(call.call_id, call.company_name) for call in calls] == [
            ("Example_Bank__2.2__1", "Example Bank"),
            ("Example_Retail__2.2__1", "Example Retail"),
        ]

    def test_numbers_a_calls_quotes_in_the_user_prompt(self) -> None:
        [call] = plan_calls(
            [
                _mitigation(
                    "Example_Bank__2.2__1",
                    "recA",
                    " Our board oversees AI.\n",
                    "The risk committee reviews AI risks.",
                )
            ],
            companies=COMPANIES,
        )

        assert call.user_prompt(PROMPT) == (
            "Example Bank|Example_Bank__2.2__1\n"
            + '<quote id="1">Our board oversees AI.</quote>\n'
            + '<quote id="2">The risk committee reviews AI risks.</quote>'
        )


def _response(practice: str, *subtypes: str) -> StructuredResult[Answer]:
    return StructuredResult(
        value=Answer(
            match_id="Example_Bank__2.2__1",
            classifications=[
                TaggedPractice(
                    practice=practice,
                    subtypes=list(subtypes),
                    quotes=[1],
                    reasoning="The board oversees AI.",
                )
            ],
            affiliations=[],
        ),
        model=STUB_MODEL,
        usage=STUB_USAGE,
    )


class TestMakePracticesResult:
    def test_keeps_an_answer_whose_names_are_listed(self) -> None:
        response = _response(
            "Formal AI oversight and accountability", "Board of directors oversight"
        )

        assert make_practices_result(
            CALL, response, practices=PRACTICES
        ) == PracticesResult(
            mitigation_id="Example_Bank__2.2__1",
            answer=response.value,
            model=STUB_MODEL,
            usage=STUB_USAGE,
        )

    def test_rejects_an_answer_with_unlisted_names(self) -> None:
        response = _response("Board oversight")

        with pytest.raises(
            ToolboxLLMInvalidResponseError, match="practice 'Board oversight'"
        ):
            make_practices_result(CALL, response, practices=PRACTICES)
