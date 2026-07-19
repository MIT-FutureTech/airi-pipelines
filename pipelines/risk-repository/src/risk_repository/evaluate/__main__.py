import asyncio
import logging

from risk_repository.evaluate.extract import evaluate_extraction
from risk_repository.evaluate.ground_truth import (
    fetch_ground_truth,
    fetch_screening_ground_truth,
)
from risk_repository.evaluate.match import match_all
from risk_repository.evaluate.report import print_report
from risk_repository.evaluate.screen import evaluate_screening
from risk_repository.evaluate.settings import EvaluationSettings
from toolbox.airtable import AirtableClient
from toolbox.llm import OpenRouterClient
from toolbox.log import configure_logging


async def main() -> None:
    settings = EvaluationSettings()
    configure_logging(level=logging.INFO, loggers_to_silence=["httpx", "openai"])

    async with AirtableClient(timeout=settings.airtable_timeout) as airtable:
        screening_ground_truth = await fetch_screening_ground_truth(
            client=airtable,
            base_id=settings.airtable_base_id,
            table_name=settings.screening_ground_truth_table,
        )
        ground_truth = await fetch_ground_truth(
            airtable,
            base_id=settings.airtable_base_id,
            documents_table_name=settings.extraction_ground_truth_table,
        )

    screening = evaluate_screening(screening_ground_truth, settings.results_dir)

    async with OpenRouterClient(
        model=settings.model,
        rate_limit_rps=settings.llm_rate_limit_rps,
        timeout=settings.llm_timeout,
        temperature=0.0,
    ) as llm:
        match_results = await match_all(
            ground_truth,
            settings.results_dir,
            llm,
            concurrency=settings.concurrency,
            max_attempts=settings.max_attempts,
        )
    extraction = evaluate_extraction(match_results)

    print_report(screening=screening, extraction=extraction, classification=None)


if __name__ == "__main__":
    asyncio.run(main())
