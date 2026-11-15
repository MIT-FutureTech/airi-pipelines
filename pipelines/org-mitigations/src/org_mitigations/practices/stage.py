import logging
from functools import partial

from org_mitigations.companies import Company
from org_mitigations.llm_calls import make_llm_client, preview_calls, run_calls
from org_mitigations.practice_list import (
    PRACTICE_LIST_PATH,
    load_practice_list,
    render_practice_list,
)
from org_mitigations.practices.answer import Answer
from org_mitigations.practices.calls import (
    PracticesResult,
    make_practices_result,
    plan_calls,
)
from org_mitigations.prompt import load_prompt
from org_mitigations.search.calls import SearchResult
from org_mitigations.search.context import Context
from org_mitigations.search.mitigations import mitigations_from_results
from org_mitigations.settings import PipelineSettings, PipelineStage
from toolbox.results import ResultStore

logger = logging.getLogger(__name__)


async def run_practices(
    contexts: list[Context],
    *,
    companies: list[Company],
    settings: PipelineSettings,
) -> None:
    context_ids = {context.context_id for context in contexts}
    search_store = ResultStore(settings.output_dir / PipelineStage.SEARCH, SearchResult)
    search_results = {
        call_id: result
        for call_id, result in search_store.load_all().items()
        if result.context_id in context_ids
    }
    mitigations = mitigations_from_results(search_results, contexts)
    calls = plan_calls(mitigations, companies=companies)
    logger.info(
        f"{len(search_results)} search results found {len(mitigations)} mitigations,"
        + " one call each"
    )

    practices = load_practice_list(PRACTICE_LIST_PATH)
    prompt = load_prompt(
        settings.practices.prompt_path,
        practices=render_practice_list(practices),
    )
    store = ResultStore(settings.output_dir / PipelineStage.PRACTICES, PracticesResult)
    if settings.dry_run:
        preview_calls(calls, prompt=prompt, store=store)
        return

    async with make_llm_client(settings.practices, settings=settings) as llm:
        await run_calls(
            calls,
            prompt=prompt,
            answer_schema=Answer,
            make_result=partial(make_practices_result, practices=practices),
            llm=llm,
            store=store,
            max_concurrency=settings.concurrency,
        )
