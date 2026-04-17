import argparse
import asyncio
import logging
from pathlib import Path

from risk_repository.evaluate.classify import evaluate_classification
from risk_repository.evaluate.extract import evaluate_extraction
from risk_repository.evaluate.ground_truth import fetch_ground_truth
from risk_repository.evaluate.match import match_all
from risk_repository.evaluate.report import print_report
from risk_repository.evaluate.screen import evaluate_screening
from toolbox.airtable import Client as AirtableClient
from toolbox.llm import OpenAIClient
from toolbox.log import configure_logging

DEFAULT_RESULTS_DIR = Path("output")
DEFAULT_MODEL = "gpt-5-mini-2025-08-07"
AIRTABLE_TIMEOUT = 30.0
LLM_RATE_LIMIT_RPS = 10.0
LLM_TIMEOUT = 120.0


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Evaluate AI Risk Repository pipeline against Airtable ground truth"
    )
    parser.add_argument("--results-dir", type=Path, default=DEFAULT_RESULTS_DIR)
    parser.add_argument("--model", default=DEFAULT_MODEL)
    return parser.parse_args()


async def amain() -> None:
    args = _parse_args()
    configure_logging(level=logging.INFO, loggers_to_silence=["httpx", "openai"])

    async with AirtableClient(timeout=AIRTABLE_TIMEOUT) as airtable:
        gt = await fetch_ground_truth(airtable)

    gt_quick_refs = {doc.quick_ref for doc in gt.documents}
    screening = evaluate_screening(gt_quick_refs, args.results_dir)

    async with OpenAIClient(
        model=args.model,
        rate_limit_rps=LLM_RATE_LIMIT_RPS,
        timeout=LLM_TIMEOUT,
    ) as llm:
        match_results = await match_all(gt, args.results_dir, llm)

    extraction = evaluate_extraction(match_results)
    classification = evaluate_classification(match_results, args.results_dir)
    print_report(screening, extraction, classification)


if __name__ == "__main__":
    asyncio.run(amain())
