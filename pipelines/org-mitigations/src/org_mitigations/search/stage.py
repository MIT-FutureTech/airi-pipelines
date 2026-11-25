import logging

from org_mitigations.companies import Company
from org_mitigations.domain_taxonomy import (
    DOMAIN_TAXONOMY_PATH,
    load_domain_taxonomy,
    render_domain_taxonomy,
)
from org_mitigations.llm_calls import make_llm_client, preview_calls, run_calls
from org_mitigations.prompt import load_prompt
from org_mitigations.search.answer import Answer
from org_mitigations.search.calls import SearchResult, make_search_result, plan_calls
from org_mitigations.search.context import Context
from org_mitigations.settings import PipelineSettings, PipelineStage
from toolbox.results import ResultStore

logger = logging.getLogger(__name__)


async def run_search(
    contexts: list[Context],
    *,
    companies: list[Company],
    settings: PipelineSettings,
) -> None:
    domain_codes = [
        domain.code
        for locus in load_domain_taxonomy(DOMAIN_TAXONOMY_PATH)
        for domain in locus.domains
    ]
    calls = plan_calls(contexts, domain_codes, companies=companies)
    covered = {context.company_id for context in contexts}
    logger.info(
        f"{len(covered)} of {len(companies)} companies have passages:"
        + f" {len(contexts)} contexts, {len(calls)} calls"
    )

    prompt = load_prompt(
        settings.search.prompt_path,
        taxonomy=render_domain_taxonomy(DOMAIN_TAXONOMY_PATH),
    )
    store = ResultStore(settings.output_dir / PipelineStage.SEARCH, SearchResult)
    if settings.dry_run:
        preview_calls(calls, prompt=prompt, store=store)
        return

    async with make_llm_client(settings.search, settings=settings) as llm:
        await run_calls(
            calls,
            prompt=prompt,
            answer_schema=Answer,
            make_result=make_search_result,
            llm=llm,
            store=store,
            max_concurrency=settings.concurrency,
        )
