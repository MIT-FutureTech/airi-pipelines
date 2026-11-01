from collections.abc import Sequence
from pathlib import Path

from org_mitigations.answer import Answer
from org_mitigations.calls import CallResult, plan_calls, run_calls
from org_mitigations.companies import Company
from org_mitigations.context import Context
from org_mitigations.prompt import Prompt
from toolbox.llm import Message, ToolboxLLMInvalidResponseError
from toolbox.llm.stub import STUB_MODEL, STUB_USAGE, StubLLMClient
from toolbox.results import ResultStore

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


def _stub(*, failing: set[str]) -> StubLLMClient:
    def answer(messages: Sequence[Message]) -> Answer:
        _, _, match_id, _ = messages[-1].content.split("|")
        if match_id in failing:
            raise ToolboxLLMInvalidResponseError("LLM did not generate response")
        return Answer(
            match_id=match_id,
            has_mitigation=False,
            reason="Nothing in this category",
            classifications=[],
        )

    return StubLLMClient(answer)


async def _run(llm: StubLLMClient, store: ResultStore[CallResult]) -> None:
    await run_calls(
        plan_calls(CONTEXTS, ["1.1", "2.1"], companies=COMPANIES),
        prompt=PROMPT,
        llm=llm,
        store=store,
        max_concurrency=2,
    )


class TestPlanCalls:
    def test_makes_a_call_for_each_context_and_code(self) -> None:
        calls = plan_calls(CONTEXTS, ["1.1", "2.1"], companies=COMPANIES)

        assert [(call.call_id, call.company) for call in calls] == [
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


class TestRunCalls:
    async def test_saves_a_result_for_each_context_and_code(
        self, tmp_path: Path
    ) -> None:
        store = ResultStore(tmp_path / "calls", CallResult)

        await _run(_stub(failing=set()), store)

        assert sorted(store.load_all()) == [
            "Example_Bank__1.1",
            "Example_Bank__2.1",
            "Example_Retail__1.1",
            "Example_Retail__2.1",
        ]
        assert store.load("Example_Bank__2.1") == CallResult(
            context_id="Example_Bank",
            code="2.1",
            answer=Answer(
                match_id="Example_Bank__2.1",
                has_mitigation=False,
                reason="Nothing in this category",
                classifications=[],
            ),
            model=STUB_MODEL,
            usage=STUB_USAGE,
        )

    async def test_sends_the_system_prompt_and_the_filled_in_user_prompt(
        self, tmp_path: Path
    ) -> None:
        llm = _stub(failing=set())

        await _run(llm, ResultStore(tmp_path / "calls", CallResult))

        assert [
            Message(role="system", content="Find mitigations."),
            Message(
                role="user",
                content="Example Retail|2.1|Example_Retail__2.1|<document>retail</document>",
            ),
        ] in llm.messages

    async def test_skips_calls_that_have_a_result(self, tmp_path: Path) -> None:
        store = ResultStore(tmp_path / "calls", CallResult)
        await _run(_stub(failing=set()), store)
        llm = _stub(failing=set())

        await _run(llm, store)

        assert llm.messages == []

    async def test_saves_nothing_for_a_call_without_a_usable_answer(
        self, tmp_path: Path
    ) -> None:
        store = ResultStore(tmp_path / "calls", CallResult)

        await _run(_stub(failing={"Example_Bank__1.1"}), store)

        assert not store.has("Example_Bank__1.1")
        assert len(store.load_all()) == 3
