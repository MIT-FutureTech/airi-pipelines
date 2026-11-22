import re

import pytest

from org_mitigations.instrument_taxonomy import Instrument, Modality
from org_mitigations.instruments.answer import Answer
from org_mitigations.instruments.calls import (
    Call,
    InstrumentsResult,
    make_instruments_result,
    plan_calls,
)
from org_mitigations.prompt import Prompt
from org_mitigations.search.answer import Strength
from org_mitigations.search.mitigations import FoundMitigation, FoundQuote
from toolbox.llm import StructuredResult, ToolboxLLMInvalidResponseError
from toolbox.llm.stub import STUB_MODEL, STUB_USAGE

PROMPT = Prompt(
    system="Classify instruments.",
    user_template="$context_mitigations\n---\n$name|$description\n$evidence",
)
MODALITIES = [
    Modality(
        code="2",
        name="Govern",
        instruments=[Instrument(code="2.3", name="Internal Policies")],
    ),
]


def _mitigation(mitigation_id: str, name: str, *quotes: str) -> FoundMitigation:
    context_id, domain_code, _ = mitigation_id.split("__")
    return FoundMitigation(
        mitigation_id=mitigation_id,
        context_id=context_id,
        company_id="recA",
        domain_code=domain_code,
        name=name,
        reasoning=f"Why {name}",
        quotes=[
            FoundQuote(
                excerpt_id=f"{mitigation_id}_excerpt1",
                quote=quote,
                strength=Strength.STATED,
            )
            for quote in quotes
        ],
    )


BOARD = _mitigation("Bank_group1__2.2__1", "Board oversight", "Our board oversees AI.")
POLICY = _mitigation("Bank_group1__3.1__1", "AI policy", "We publish an AI policy.")
RED_TEAM = _mitigation("Bank_group2__1.4__1", "Red teaming", "We red-team models.")


class TestPlanCalls:
    def test_lists_the_mitigations_from_the_same_context(self) -> None:
        calls = plan_calls([BOARD, POLICY, RED_TEAM])

        assert [
            (
                call.call_id,
                [other.mitigation_id for other in call.context_mitigations],
            )
            for call in calls
        ] == [
            ("Bank_group1__2.2__1", ["Bank_group1__2.2__1", "Bank_group1__3.1__1"]),
            ("Bank_group1__3.1__1", ["Bank_group1__2.2__1", "Bank_group1__3.1__1"]),
            ("Bank_group2__1.4__1", ["Bank_group2__1.4__1"]),
        ]

    def test_marks_the_mitigation_to_classify_in_the_user_prompt(self) -> None:
        mitigation = _mitigation(
            "Bank_group1__3.1__1",
            "AI policy",
            " We publish an AI policy.\n",
            "Staff must follow it.",
        )
        call = Call(mitigation=mitigation, context_mitigations=[BOARD, mitigation])

        assert call.user_prompt(PROMPT) == (
            "- Board oversight: Why Board oversight\n"
            + "- AI policy: Why AI policy <-- THIS MITIGATION (classify this one)\n"
            + "---\n"
            + "AI policy|Why AI policy\n"
            + "<quote>We publish an AI policy.</quote>\n"
            + "<quote>Staff must follow it.</quote>"
        )


def _response(modality: str, instrument_code: str) -> StructuredResult[Answer]:
    return StructuredResult(
        value=Answer(
            lever="Creating a rule for itself.",
            modality=modality,
            instrument_code=instrument_code,
            reasoning="Self-authored internal rule.",
        ),
        model=STUB_MODEL,
        usage=STUB_USAGE,
    )


class TestMakeInstrumentsResult:
    def test_keeps_an_answer_with_a_valid_code(self) -> None:
        call = Call(mitigation=POLICY, context_mitigations=[BOARD, POLICY])
        response = _response("2", "2.3")

        assert make_instruments_result(
            call, response, modalities=MODALITIES
        ) == InstrumentsResult(
            mitigation_id="Bank_group1__3.1__1",
            answer=response.value,
            model=STUB_MODEL,
            usage=STUB_USAGE,
        )

    def test_rejects_an_answer_with_an_invalid_code(self) -> None:
        call = Call(mitigation=POLICY, context_mitigations=[BOARD, POLICY])

        with pytest.raises(ToolboxLLMInvalidResponseError, match=re.escape("'2.4'")):
            make_instruments_result(call, _response("2", "2.4"), modalities=MODALITIES)
