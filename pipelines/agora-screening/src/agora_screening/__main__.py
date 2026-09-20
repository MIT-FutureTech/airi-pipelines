import asyncio
import logging

from agora_screening.corpus import apply_selection, load_oecd_corpus, select_with_text
from agora_screening.export import export_csv
from agora_screening.prompts import build_system_prompt, load_rubric
from agora_screening.score import run_scoring
from agora_screening.settings import AgoraScreeningSettings
from toolbox.llm import OpenRouterClient
from toolbox.log import configure_logging, install_log_context_filter

logger = logging.getLogger(__name__)


async def main() -> None:
    settings = AgoraScreeningSettings()
    settings.output_dir.mkdir(parents=True, exist_ok=True)
    configure_logging(
        level=logging.INFO,
        filepath=settings.log_path or settings.output_dir / "log.txt",
        loggers_to_silence=["httpx", "openai"],
    )
    try:
        logger.info(f"Configuration: {settings.model_dump_json()}")
        install_log_context_filter()

        corpus = load_oecd_corpus(settings.corpus_path)
        records = apply_selection(
            select_with_text(corpus, settings.min_chars),
            document_ids=settings.document_ids,
            limit=settings.limit,
        )
        logger.info(f"Scoring {len(records)} documents")

        system_prompt = build_system_prompt(load_rubric(settings.rubric_path))

        async with OpenRouterClient(
            model=settings.model,
            rate_limit_rps=settings.llm_rate_limit_rps,
            timeout=settings.llm_timeout,
            temperature=settings.temperature,
        ) as llm:
            await run_scoring(
                records, llm=llm, system_prompt=system_prompt, settings=settings
            )

        if settings.export_csv is not None:
            _ = export_csv(
                records, output_dir=settings.output_dir, csv_path=settings.export_csv
            )
    except:
        logger.exception("Uncaught exception")
        raise


if __name__ == "__main__":
    asyncio.run(main())
