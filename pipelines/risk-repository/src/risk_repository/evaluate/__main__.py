import asyncio
import logging

from risk_repository.evaluate.classify import evaluate_classification
from risk_repository.evaluate.extract import evaluate_extraction
from risk_repository.evaluate.ground_truth import fetch_ground_truth
from risk_repository.evaluate.match import match_all
from risk_repository.evaluate.report import print_report
from risk_repository.evaluate.screen import evaluate_screening
from risk_repository.settings import EvaluationSettings
from toolbox.airtable import AirtableClient
from toolbox.llm import OpenAIClient
from toolbox.log import configure_logging


async def amain() -> None:
    settings = EvaluationSettings()
    configure_logging(level=logging.INFO, loggers_to_silence=["httpx", "openai"])

    async with AirtableClient(timeout=settings.airtable_timeout) as airtable:
        ground_truth = await fetch_ground_truth(
            client=airtable,
            base_id=settings.airtable_base_id,
            documents_table_name=settings.airtable_documents_table,
        )

    gt_quick_refs = {doc.quick_ref for doc in ground_truth.documents}
    screening = evaluate_screening(gt_quick_refs, settings.results_dir)

    async with OpenAIClient(
        model=settings.model,
        rate_limit_rps=settings.llm_rate_limit_rps,
        timeout=settings.llm_timeout,
    ) as llm:
        match_results = await match_all(
            ground_truth=ground_truth,
            results_dir=settings.results_dir,
            llm=llm,
            concurrency=settings.concurrency,
            max_attempts=settings.max_attempts,
        )

    extraction = evaluate_extraction(match_results)
    classification = evaluate_classification(match_results, settings.results_dir)
    print_report(screening, extraction, classification)


if __name__ == "__main__":
    asyncio.run(amain())
