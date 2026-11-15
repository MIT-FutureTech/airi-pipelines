import logging
from collections.abc import Callable
from typing import Protocol

from pydantic import BaseModel

from org_mitigations.prompt import Prompt
from org_mitigations.settings import PipelineSettings, StageSettings
from toolbox.classification import LLMClassifier
from toolbox.concurrency import ConcurrentMap
from toolbox.llm import (
    LLMClient,
    OpenRouterClient,
    StructuredResult,
    ToolboxLLMInvalidResponseError,
)
from toolbox.log import log_context
from toolbox.results import ResultStore

logger = logging.getLogger(__name__)


class LLMCall(Protocol):
    @property
    def call_id(self) -> str: ...

    def user_prompt(self, prompt: Prompt) -> str: ...


def make_llm_client(
    stage: StageSettings,
    *,
    settings: PipelineSettings,
) -> OpenRouterClient:
    return OpenRouterClient(
        model=stage.model,
        rate_limit_rps=settings.llm_rate_limit_rps,
        timeout=settings.llm_timeout,
        temperature=stage.temperature,
        reasoning_effort=stage.reasoning_effort,
        output_token_limit=stage.output_token_limit,
    )


async def run_calls[C: LLMCall, A: BaseModel, R: BaseModel](
    calls: list[C],
    *,
    prompt: Prompt,
    answer_schema: type[A],
    make_result: Callable[[C, StructuredResult[A]], R],
    llm: LLMClient,
    store: ResultStore[R],
    max_concurrency: int,
) -> None:
    pending = [call for call in calls if not store.has(call.call_id)]
    if len(calls) != len(pending):
        logger.info(f"{len(calls) - len(pending)} of {len(calls)} calls have a result")

    classifier = LLMClassifier(
        llm, system_prompt=prompt.system, response_schema=answer_schema
    )
    runner = ConcurrentMap(
        max_concurrency=max_concurrency,
        progress_description="Calls",
    )
    async for _ in runner.map(
        pending,
        _make_call,
        prompt=prompt,
        classifier=classifier,
        make_result=make_result,
        store=store,
    ):
        pass


def preview_calls[C: LLMCall, R: BaseModel](
    calls: list[C],
    *,
    prompt: Prompt,
    store: ResultStore[R],
) -> None:
    pending = [call for call in calls if not store.has(call.call_id)]
    if len(calls) != len(pending):
        print(f"{len(calls) - len(pending)} of {len(calls)} calls have a result")
    if not pending:
        return
    print(f"\n=== System prompt ===\n{prompt.system}")
    print(
        f"\n=== User prompt for {pending[0].call_id} ===\n{pending[0].user_prompt(prompt)}"
    )


async def _make_call[C: LLMCall, A: BaseModel, R: BaseModel](
    call: C,
    *,
    prompt: Prompt,
    classifier: LLMClassifier[A],
    make_result: Callable[[C, StructuredResult[A]], R],
    store: ResultStore[R],
) -> None:
    with log_context(call_id=call.call_id):
        try:
            response = await classifier.classify(call.user_prompt(prompt))
            result = make_result(call, response)
        except ToolboxLLMInvalidResponseError as error:
            logger.warning(f"No usable answer, so no result saved: {error!r}")
            return
        store.save(call.call_id, result)
