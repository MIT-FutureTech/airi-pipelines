import asyncio
import logging

from org_mitigations.calls import Call, CallResult, plan_calls, run_calls
from org_mitigations.companies import Company, load_companies
from org_mitigations.context import build_contexts
from org_mitigations.documents import load_documents
from org_mitigations.excerpts import merge_passages
from org_mitigations.passages import load_passages
from org_mitigations.prompt import Prompt, load_prompt
from org_mitigations.settings import PipelineSettings
from org_mitigations.taxonomy import TAXONOMY_PATH, load_taxonomy, render_taxonomy
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

        companies = _select_companies(
            load_companies(settings.export_dir),
            settings.company_names,
        )
        company_ids = {company.company_id for company in companies}
        documents = [
            document
            for document in load_documents(settings.export_dir)
            if document.company_id in company_ids
        ]
        document_ids = {document.document_id for document in documents}
        passages = [
            passage
            for passage in load_passages(settings.export_dir)
            if passage.document_id in document_ids
        ]
        contexts = build_contexts(
            merge_passages(passages),
            documents,
            max_chars=settings.max_chars,
        )
        codes = [
            code.code for locus in load_taxonomy(TAXONOMY_PATH) for code in locus.codes
        ]
        calls = plan_calls(contexts, codes, companies=companies)
        covered = {context.company_id for context in contexts}
        logger.info(
            f"{len(covered)} of {len(companies)} companies have passages:"
            + f" {len(contexts)} contexts, {len(calls)} calls"
        )

        prompt = load_prompt(
            settings.prompt_path,
            taxonomy=render_taxonomy(TAXONOMY_PATH),
        )
        store = ResultStore(settings.output_dir / "calls", CallResult)
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


def _select_companies(
    all_companies: list[Company],
    selected_names: list[str] | None,
) -> list[Company]:
    if selected_names is None:
        return all_companies
    companies_by_name = {company.name: company for company in all_companies}
    unknown = [name for name in selected_names if name not in companies_by_name]
    if unknown:
        raise ValueError(f"No companies named {unknown}")
    return [companies_by_name[name] for name in selected_names]


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
