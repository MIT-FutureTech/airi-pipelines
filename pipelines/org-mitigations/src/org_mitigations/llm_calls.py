import logging

from org_mitigations.prompt import Prompt
from org_mitigations.search.answer import Answer
from org_mitigations.search.calls import Call, SearchResult, make_search_result
from toolbox.classification import LLMClassifier
from toolbox.concurrency import ConcurrentMap
from toolbox.llm import LLMClient, ToolboxLLMInvalidResponseError
from toolbox.log import log_context
from toolbox.results import ResultStore

logger = logging.getLogger(__name__)


async def run_calls(
    calls: list[Call],
    *,
    prompt: Prompt,
    llm: LLMClient,
    store: ResultStore[SearchResult],
    max_concurrency: int,
) -> None:
    pending = [call for call in calls if not store.has(call.call_id)]
    if len(calls) != len(pending):
        logger.info(f"{len(calls) - len(pending)} of {len(calls)} calls have a result")

    classifier = LLMClassifier(llm, system_prompt=prompt.system, response_schema=Answer)
    runner = ConcurrentMap(
        max_concurrency=max_concurrency,
        progress_description="Calls",
    )
    async for _ in runner.map(
        pending,
        _make_call,
        prompt=prompt,
        classifier=classifier,
        store=store,
    ):
        pass


async def _make_call(
    call: Call,
    *,
    prompt: Prompt,
    classifier: LLMClassifier[Answer],
    store: ResultStore[SearchResult],
) -> None:
    with log_context(call_id=call.call_id):
        try:
            response = await classifier.classify(call.user_prompt(prompt))
        except ToolboxLLMInvalidResponseError as error:
            logger.warning(f"No usable answer, so no result saved: {error!r}")
            return
        store.save(call.call_id, make_search_result(call, response))
