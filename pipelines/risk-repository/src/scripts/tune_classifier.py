r"""Score the classifier against the previous iteration of the risk repository.

Classifies curated risks directly from Airtable, not risks extracted by the
pipeline.

Usage example:

    uv run --env-file=../../.env python src/scripts/tune_classifier.py \
        --output output/classifier_baseline.json --view "Dev set"
"""

import argparse
import asyncio
import logging
from pathlib import Path

from pydantic import BaseModel

from risk_repository.classify import ClassifiedRisk, classify_risks, codable_risks
from risk_repository.evaluate.classify import (
    AxisMetrics,
    Labels,
    ground_truth_labels,
    ground_truth_nodes,
    predicted_labels,
    score_classifications,
)
from risk_repository.evaluate.ground_truth import (
    GroundTruthRisk,
    fetch_ground_truth_risks,
)
from risk_repository.settings import (
    DEFAULT_AIRTABLE_BASE_ID,
    DEFAULT_AIRTABLE_TIMEOUT,
    DEFAULT_CONCURRENCY,
    DEFAULT_LLM_RATE_LIMIT_RPS,
    DEFAULT_MODEL,
)
from toolbox.airtable import AirtableClient
from toolbox.llm import OpenRouterClient
from toolbox.log import configure_logging

logger = logging.getLogger(__name__)

AXES = ("entity", "intent", "timing", "subdomain")


class RiskComparison(BaseModel):
    ev_id: str
    document_readable_id: str
    name: str
    description: str
    ground_truth: Labels
    predicted: Labels
    disagreements: list[str]
    causal_reasoning: str
    domain_reasoning: str


class TuningRun(BaseModel):
    model: str
    view: str | None
    risks: int
    axes: list[AxisMetrics]
    comparisons: list[RiskComparison]


def _compare(gt_risk: GroundTruthRisk, classified: ClassifiedRisk) -> RiskComparison:
    truth = ground_truth_labels(gt_risk)
    predicted = predicted_labels(classified)
    return RiskComparison(
        ev_id=gt_risk.ev_id,
        document_readable_id=gt_risk.document_readable_id,
        name=gt_risk.subcategory or gt_risk.category,
        description=gt_risk.description,
        ground_truth=truth,
        predicted=predicted,
        disagreements=[
            axis for axis in AXES if getattr(truth, axis) != getattr(predicted, axis)
        ],
        causal_reasoning=classified.causal.reasoning,
        domain_reasoning=classified.domain.reasoning,
    )


def _print_report(run: TuningRun) -> None:
    print(f"\nModel: {run.model}")
    print(f"View: {run.view or '(all risks)'}")
    print(f"Risks classified: {run.risks}")
    print(f"\n{'Axis':<12}{'Total':>8}{'Correct':>9}{'Accuracy':>10}{'Kappa':>8}")
    for axis in run.axes:
        accuracy = f"{axis.accuracy:.3f}"
        kappa = f"{axis.kappa:.3f}"
        print(
            f"{axis.axis:<12}{axis.total:>8}{axis.correct:>9}{accuracy:>10}{kappa:>8}"
        )
    disagreed = sum(1 for c in run.comparisons if c.disagreements)
    print(f"\nRisks disagreeing on at least one axis: {disagreed}/{run.risks}")


async def main() -> None:
    args = _parse_args()
    configure_logging(level=logging.INFO, loggers_to_silence=["httpx", "openai"])

    async with AirtableClient(timeout=DEFAULT_AIRTABLE_TIMEOUT) as airtable:
        gt_risks = await fetch_ground_truth_risks(
            airtable, base_id=args.base_id, view=args.view
        )
    by_ev_id = {risk.ev_id: risk for risk in gt_risks}
    if len(by_ev_id) != len(gt_risks):
        raise ValueError("Ground-truth risks do not have unique Ev_IDs")
    logger.info(f"Classifying {len(gt_risks)} risks")

    async with OpenRouterClient(
        model=args.model,
        rate_limit_rps=args.rate_limit_rps,
    ) as llm:
        classified = [
            result
            async for result in classify_risks(
                codable_risks(
                    node for risk in gt_risks for node in ground_truth_nodes(risk)
                ),
                llm=llm,
                concurrency=args.concurrency,
                progress_description="Classifying",
            )
        ]

    pairs = [(by_ev_id[result.risk_id], result) for result in classified]
    run = TuningRun(
        model=args.model,
        view=args.view,
        risks=len(pairs),
        axes=score_classifications(pairs),
        comparisons=[_compare(gt_risk, result) for gt_risk, result in pairs],
    )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(run.model_dump_json(indent=2))
    _print_report(run)
    print(f"\nWrote {args.output}")


class _HelpFormatter(
    argparse.ArgumentDefaultsHelpFormatter,
    argparse.RawDescriptionHelpFormatter,
):
    pass


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=_HelpFormatter
    )
    parser.add_argument(
        "--output",
        type=Path,
        required=True,
        help="Path to write this run's metrics and per-risk comparisons",
    )
    parser.add_argument(
        "--view",
        default=None,
        help="Airtable view narrowing which curated risks to classify",
    )
    parser.add_argument(
        "--model",
        default=DEFAULT_MODEL,
        help="LLM model to use for classification",
    )
    parser.add_argument(
        "--concurrency",
        type=int,
        default=DEFAULT_CONCURRENCY,
        help="Number of risks to classify at once",
    )
    parser.add_argument(
        "--rate-limit-rps",
        type=float,
        default=DEFAULT_LLM_RATE_LIMIT_RPS,
        help="Maximum LLM requests per second",
    )
    parser.add_argument(
        "--base-id",
        default=DEFAULT_AIRTABLE_BASE_ID,
        help="Airtable base holding the AI Risk Database",
    )
    return parser.parse_args()


if __name__ == "__main__":
    asyncio.run(main())
