import asyncio
import logging

from org_mitigations.corpus import load_corpus
from org_mitigations.practices.stage import run_practices
from org_mitigations.search.context import build_contexts
from org_mitigations.search.stage import run_search
from org_mitigations.settings import PipelineSettings, PipelineStage
from toolbox.log import configure_logging, install_log_context_filter

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
        if PipelineStage.SEARCH in settings.stages:
            await run_search(contexts, companies=corpus.companies, settings=settings)
        if PipelineStage.PRACTICES in settings.stages:
            await run_practices(contexts, companies=corpus.companies, settings=settings)
    except:
        logger.exception("Uncaught exception")
        raise


if __name__ == "__main__":
    asyncio.run(main())
