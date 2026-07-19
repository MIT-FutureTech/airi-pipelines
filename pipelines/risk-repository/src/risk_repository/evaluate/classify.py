import logging
from collections import Counter
from pathlib import Path

from pydantic import BaseModel

from risk_repository.classify import (
    ClassificationResult,
    Entity,
    Intent,
    Subdomain,
    Timing,
)
from risk_repository.evaluate.match import DocumentMatchResult
from risk_repository.results import PipelineStage, load, result_path

logger = logging.getLogger(__name__)


def _subdomain_code(subdomain: Subdomain) -> str | None:
    """Map a predicted subdomain to a code, or None when unclassified (X.1)."""
    if subdomain is Subdomain.UNCLASSIFIED:
        return None
    return subdomain.value


def _domain_code(subdomain_code: str | None) -> str | None:
    """Reduce a subdomain code like "3.1" to its parent domain "3"."""
    if subdomain_code is None:
        return None
    return subdomain_code.split(".", 1)[0]


class AxisMetrics(BaseModel):
    axis: str
    total: int
    correct: int
    accuracy: float
    kappa: float


class ClassificationMetrics(BaseModel):
    matched_risks: int
    axes: list[AxisMetrics]


def evaluate_classification(
    match_results: list[DocumentMatchResult],
    results_dir: Path,
) -> ClassificationMetrics:
    entity_pairs: list[tuple[Entity | None, Entity | None]] = []
    intent_pairs: list[tuple[Intent | None, Intent | None]] = []
    timing_pairs: list[tuple[Timing | None, Timing | None]] = []
    domain_pairs: list[tuple[str | None, str | None]] = []
    subdomain_pairs: list[tuple[str | None, str | None]] = []
    matched_risks = 0

    for doc in match_results:
        classification_path = result_path(
            results_dir, PipelineStage.CLASSIFY, doc.readable_id
        )
        if not classification_path.exists():
            continue
        classification = load(classification_path, ClassificationResult)

        for match in doc.matches:
            gt_risk = doc.gt_risks[match.gt_index]
            if match.pipeline_index >= len(classification.risks):
                logger.warning(
                    f"{doc.readable_id}: pipeline index {match.pipeline_index} out of range for classification results"
                )
                continue
            pipeline_risk = classification.risks[match.pipeline_index]
            pipeline_causal = pipeline_risk.causal
            matched_risks += 1

            gt_entity = Entity(gt_risk.entity.lower()) if gt_risk.entity else None
            gt_intent = Intent(gt_risk.intent.lower()) if gt_risk.intent else None
            gt_timing = Timing(gt_risk.timing.lower()) if gt_risk.timing else None

            entity_pairs.append((gt_entity, pipeline_causal.entity))
            intent_pairs.append((gt_intent, pipeline_causal.intent))
            timing_pairs.append((gt_timing, pipeline_causal.timing))

            gt_subdomain = gt_risk.subdomain_code
            pl_subdomain = _subdomain_code(pipeline_risk.domain.subdomain)
            subdomain_pairs.append((gt_subdomain, pl_subdomain))
            domain_pairs.append(
                (_domain_code(gt_subdomain), _domain_code(pl_subdomain))
            )

    return ClassificationMetrics(
        matched_risks=matched_risks,
        axes=[
            _compute_axis_metrics("Entity", entity_pairs),
            _compute_axis_metrics("Intent", intent_pairs),
            _compute_axis_metrics("Timing", timing_pairs),
            _compute_axis_metrics("Domain", domain_pairs),
            _compute_axis_metrics("Subdomain", subdomain_pairs),
        ],
    )


def _compute_axis_metrics[T](
    axis: str,
    pairs: list[tuple[T | None, T | None]],
) -> AxisMetrics:
    if not pairs:
        return AxisMetrics(axis=axis, total=0, correct=0, accuracy=0.0, kappa=0.0)

    total = len(pairs)
    correct = sum(1 for gt, pl in pairs if gt == pl)
    accuracy = correct / total

    gt_counts: Counter[T | None] = Counter(gt for gt, _ in pairs)
    pl_counts: Counter[T | None] = Counter(pl for _, pl in pairs)
    all_labels = set(gt_counts) | set(pl_counts)
    expected_agreement = sum(
        (gt_counts[label] / total) * (pl_counts[label] / total) for label in all_labels
    )

    if expected_agreement == 1.0:
        kappa = 1.0
    else:
        kappa = (accuracy - expected_agreement) / (1.0 - expected_agreement)

    return AxisMetrics(
        axis=axis, total=total, correct=correct, accuracy=accuracy, kappa=kappa
    )
