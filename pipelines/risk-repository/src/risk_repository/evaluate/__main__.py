import argparse
import asyncio
import logging
from pathlib import Path

from risk_repository.evaluate.ground_truth import fetch_ground_truth
from risk_repository.evaluate.report import print_report
from risk_repository.evaluate.screen import evaluate_screening
from toolbox.airtable import Client as AirtableClient

DEFAULT_RESULTS_DIR = Path("output")
AIRTABLE_TIMEOUT = 30.0


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Evaluate AI Risk Repository pipeline against Airtable ground truth"
    )
    parser.add_argument("--results-dir", type=Path, default=DEFAULT_RESULTS_DIR)
    return parser.parse_args()


async def amain() -> None:
    args = _parse_args()
    logging.basicConfig(
        level=logging.INFO,
        style="{",
        format="{asctime:s} {levelname:7s} {name:s}:{lineno:d} {message:s}",
        datefmt="%Y-%m-%dT%H:%M:%S%z",
    )

    async with AirtableClient(timeout=AIRTABLE_TIMEOUT) as airtable:
        gt = await fetch_ground_truth(airtable)

    gt_quick_refs = {doc.quick_ref for doc in gt.documents}
    screening = evaluate_screening(gt_quick_refs, args.results_dir)
    print_report(screening)


if __name__ == "__main__":
    asyncio.run(amain())
