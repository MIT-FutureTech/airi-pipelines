import asyncio
import logging

from risk_repository.evaluate.ground_truth import fetch_screening_ground_truth
from risk_repository.evaluate.report import print_report
from risk_repository.evaluate.screen import evaluate_screening
from risk_repository.evaluate.settings import EvaluationSettings
from toolbox.airtable import AirtableClient
from toolbox.log import configure_logging


async def main() -> None:
    settings = EvaluationSettings()
    configure_logging(level=logging.INFO, loggers_to_silence=["httpx", "openai"])

    async with AirtableClient(timeout=settings.airtable_timeout) as airtable:
        screening_ground_truth = await fetch_screening_ground_truth(
            client=airtable,
            base_id=settings.airtable_base_id,
            table_name=settings.airtable_screening_table,
        )

    screening = evaluate_screening(screening_ground_truth, settings.results_dir)
    print_report(screening=screening, extraction=None, classification=None)


if __name__ == "__main__":
    asyncio.run(main())
