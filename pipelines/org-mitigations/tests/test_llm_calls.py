from collections.abc import Callable, Sequence
from pathlib import Path

import pytest

from org_mitigations.companies import Company
from org_mitigations.llm_calls import make_llm_client, run_calls
from org_mitigations.prompt import Prompt
from org_mitigations.search.answer import Answer
from org_mitigations.search.calls import (
    Call,
    SearchResult,
    make_search_result,
    plan_calls,
)
from org_mitigations.search.context import Context
from org_mitigations.settings import PipelineSettings, SearchSettings
from toolbox.llm import Message, StructuredResult, ToolboxLLMInvalidResponseError
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
            mitigations=[],
        )

    return StubLLMClient(answer)


async def _run(
    llm: StubLLMClient,
    store: ResultStore[SearchResult],
    make_result: Callable[
        [Call, StructuredResult[Answer]], SearchResult
    ] = make_search_result,
) -> None:
    await run_calls(
        plan_calls(CONTEXTS, ["1.1", "2.1"], companies=COMPANIES),
        prompt=PROMPT,
        answer_schema=Answer,
        make_result=make_result,
        llm=llm,
        store=store,
        max_concurrency=2,
    )


class TestRunCalls:
    async def test_saves_a_result_for_each_context_and_code(
        self, tmp_path: Path
    ) -> None:
        store = ResultStore(tmp_path / "calls", SearchResult)

        await _run(_stub(failing=set()), store)

        assert sorted(store.load_all()) == [
            "Example_Bank__1.1",
            "Example_Bank__2.1",
            "Example_Retail__1.1",
            "Example_Retail__2.1",
        ]
        assert store.load("Example_Bank__2.1") == SearchResult(
            context_id="Example_Bank",
            domain_code="2.1",
            answer=Answer(
                match_id="Example_Bank__2.1",
                has_mitigation=False,
                reason="Nothing in this category",
                mitigations=[],
            ),
            model=STUB_MODEL,
            usage=STUB_USAGE,
        )

    async def test_sends_the_system_prompt_and_the_filled_in_user_prompt(
        self, tmp_path: Path
    ) -> None:
        llm = _stub(failing=set())

        await _run(llm, ResultStore(tmp_path / "calls", SearchResult))

        assert [
            Message(role="system", content="Find mitigations."),
            Message(
                role="user",
                content="Example Retail|2.1|Example_Retail__2.1|<document>retail</document>",
            ),
        ] in llm.messages

    async def test_skips_calls_that_have_a_result(self, tmp_path: Path) -> None:
        store = ResultStore(tmp_path / "calls", SearchResult)
        await _run(_stub(failing=set()), store)
        llm = _stub(failing=set())

        await _run(llm, store)

        assert llm.messages == []

    async def test_saves_nothing_for_a_call_without_a_usable_answer(
        self, tmp_path: Path
    ) -> None:
        store = ResultStore(tmp_path / "calls", SearchResult)

        await _run(_stub(failing={"Example_Bank__1.1"}), store)

        assert not store.has("Example_Bank__1.1")
        assert len(store.load_all()) == 3

    async def test_saves_nothing_for_an_answer_its_stage_rejects(
        self, tmp_path: Path
    ) -> None:
        def make_result(call: Call, response: StructuredResult[Answer]) -> SearchResult:
            if call.call_id == "Example_Retail__2.1":
                raise ToolboxLLMInvalidResponseError("Names not in the list")
            return make_search_result(call, response)

        store = ResultStore(tmp_path / "calls", SearchResult)

        await _run(_stub(failing=set()), store, make_result)

        assert not store.has("Example_Retail__2.1")
        assert len(store.load_all()) == 3


class TestMakeLLMClient:
    async def test_configures_the_client_with_the_stages_settings(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("OPENROUTER_API_KEY", "sk-fake-key")
        stage = SearchSettings(
            model="example/model",
            temperature=0.5,
            reasoning_effort="low",
            output_token_limit=16_000,
        )
        settings = PipelineSettings.model_construct(
            llm_rate_limit_rps=2.0, llm_timeout=30.0
        )

        async with make_llm_client(stage, settings=settings) as llm:
            assert (
                llm._model,
                llm._temperature,
                llm._reasoning_effort,
                llm._output_token_limit,
            ) == ("example/model", 0.5, "low", 16_000)
