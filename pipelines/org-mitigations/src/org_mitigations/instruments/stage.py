import logging
from functools import partial

from org_mitigations.instrument_taxonomy import (
    INSTRUMENT_TAXONOMY_PATH,
    load_instrument_taxonomy,
    render_instrument_taxonomy,
)
from org_mitigations.instruments.answer import Answer
from org_mitigations.instruments.calls import (
    InstrumentsResult,
    make_instruments_result,
    plan_calls,
)
from org_mitigations.llm_calls import make_llm_client, preview_calls, run_calls
from org_mitigations.prompt import load_prompt
from org_mitigations.search.calls import SearchResult
from org_mitigations.search.context import Context
from org_mitigations.search.mitigations import mitigations_from_results
from org_mitigations.settings import PipelineSettings, PipelineStage
from toolbox.results import ResultStore

logger = logging.getLogger(__name__)


async def run_instruments(
    contexts: list[Context],
    *,
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
    calls = plan_calls(mitigations)
    logger.info(
        f"{len(search_results)} search results found {len(mitigations)} mitigations,"
        + " one call each"
    )

    prompt = load_prompt(
        settings.instruments.prompt_path,
        instruments=render_instrument_taxonomy(INSTRUMENT_TAXONOMY_PATH),
    )
    store = ResultStore(
        settings.output_dir / PipelineStage.INSTRUMENTS, InstrumentsResult
    )
    if settings.dry_run:
        preview_calls(calls, prompt=prompt, store=store)
        return

    async with make_llm_client(settings.instruments, settings=settings) as llm:
        await run_calls(
            calls,
            prompt=prompt,
            answer_schema=Answer,
            make_result=partial(
                make_instruments_result,
                modalities=load_instrument_taxonomy(INSTRUMENT_TAXONOMY_PATH),
            ),
            llm=llm,
            store=store,
            max_concurrency=settings.concurrency,
        )
