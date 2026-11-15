import asyncio
import logging

from org_mitigations.corpus import load_corpus
from org_mitigations.domain_taxonomy import (
    DOMAIN_TAXONOMY_PATH,
    load_domain_taxonomy,
    render_domain_taxonomy,
)
from org_mitigations.search.calls import Call, CallResult, plan_calls, run_calls
from org_mitigations.search.context import build_contexts
from org_mitigations.search.prompt import Prompt, load_prompt
from org_mitigations.settings import PipelineSettings
from toolbox.llm import OpenRouterClient
from toolbox.log import configure_logging, install_log_context_filter
from toolbox.results import ResultStore

logger = logging.getLogger(__name__)


async def main() -> None:
    settings = PipelineSettings()
    settings.output_dir.mkdir(parents=True, exist_ok=True)
    configure_logging(
        level=logging.INFO,
        filepath=settings.output_dir / "log.txt",
        loggers_to_silence=["httpx", "openai"],
    )
    try:
        logger.info(f"Configuration: {settings.model_dump_json()}")
        install_log_context_filter()

        corpus = load_corpus(settings.export_dir, company_names=settings.company_names)
        contexts = build_contexts(
            corpus.excerpts, corpus.documents, max_chars=settings.max_chars
        )
        codes = [
            code.code
            for locus in load_domain_taxonomy(DOMAIN_TAXONOMY_PATH)
            for code in locus.codes
        ]
        calls = plan_calls(contexts, codes, companies=corpus.companies)
        covered = {context.company_id for context in contexts}
        logger.info(
            f"{len(covered)} of {len(corpus.companies)} companies have passages:"
            + f" {len(contexts)} contexts, {len(calls)} calls"
        )

        prompt = load_prompt(
            settings.prompt_path,
            taxonomy=render_domain_taxonomy(DOMAIN_TAXONOMY_PATH),
        )
        store = ResultStore(settings.output_dir / "search", CallResult)
        if settings.dry_run:
            _preview(calls, prompt=prompt, store=store)
            return

        async with OpenRouterClient(
            model=settings.model,
            rate_limit_rps=settings.llm_rate_limit_rps,
            timeout=settings.llm_timeout,
            temperature=settings.temperature,
            reasoning_effort=settings.reasoning_effort,
            output_token_limit=settings.output_token_limit,
        ) as llm:
            await run_calls(
                calls,
                prompt=prompt,
                llm=llm,
                store=store,
                max_concurrency=settings.concurrency,
            )
    except:
        logger.exception("Uncaught exception")
        raise


def _preview(
    calls: list[Call],
    *,
    prompt: Prompt,
    store: ResultStore[CallResult],
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


if __name__ == "__main__":
    asyncio.run(main())
