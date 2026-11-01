import logging

from pydantic import BaseModel

from org_mitigations.answer import Answer
from org_mitigations.companies import Company
from org_mitigations.context import Context
from org_mitigations.prompt import Prompt
from toolbox.classification import LLMClassifier
from toolbox.concurrency import ConcurrentMap
from toolbox.llm import LLMClient, TokenUsage, ToolboxLLMInvalidResponseError
from toolbox.log import log_context
from toolbox.results import ResultStore

logger = logging.getLogger(__name__)


class CallResult(BaseModel):
    context_id: str
    code: str
    answer: Answer
    model: str
    usage: TokenUsage | None


class _Call(BaseModel):
    call_id: str
    company: str
    context: Context
    code: str


async def run_calls(
    contexts: list[Context],
    codes: list[str],
    *,
    companies: list[Company],
    prompt: Prompt,
    llm: LLMClient,
    store: ResultStore[CallResult],
    max_concurrency: int,
) -> None:
    company_names = {company.company_id: company.name for company in companies}
    calls = [
        _Call(
            call_id=f"{context.context_id}__{code}",
            company=company_names[context.company_id],
            context=context,
            code=code,
        )
        for context in contexts
        for code in codes
    ]
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
    call: _Call,
    *,
    prompt: Prompt,
    classifier: LLMClassifier[Answer],
    store: ResultStore[CallResult],
) -> None:
    with log_context(call_id=call.call_id):
        user_prompt = prompt.render_user(
            company=call.company,
            context=call.context.text,
            code=call.code,
            match_id=call.call_id,
        )
        try:
            result = await classifier.classify(user_prompt)
        except ToolboxLLMInvalidResponseError as error:
            logger.warning(f"No usable answer, so no result saved: {error!r}")
            return
        store.save(
            call.call_id,
            CallResult(
                context_id=call.context.context_id,
                code=call.code,
                answer=result.value,
                model=result.model,
                usage=result.usage,
            ),
        )
