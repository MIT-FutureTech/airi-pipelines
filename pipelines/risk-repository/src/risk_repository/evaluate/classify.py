import logging
from collections import Counter
from pathlib import Path

from pydantic import BaseModel

from risk_repository.classify import (
    ClassificationResult,
    Entity,
    Intent,
    Timing,
)
from risk_repository.evaluate.match import DocumentMatchResult
from risk_repository.results import PipelineStage, load, result_path

logger = logging.getLogger(__name__)


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
    entity_pairs: list[tuple[Entity | None, Entity]] = []
    intent_pairs: list[tuple[Intent | None, Intent]] = []
    timing_pairs: list[tuple[Timing | None, Timing]] = []
    matched_risks = 0

    for doc in match_results:
        classification_path = result_path(
            results_dir, PipelineStage.CLASSIFY, doc.quick_ref
        )
        if not classification_path.exists():
            continue
        classification = load(classification_path, ClassificationResult)

        for match in doc.matches:
            gt_risk = doc.gt_risks[match.gt_index]
            if match.pipeline_index >= len(classification.risks):
                logger.warning(
                    f"{doc.quick_ref}: pipeline index {match.pipeline_index} out of range for classification results"
                )
                continue
            pipeline_causal = classification.risks[match.pipeline_index].causal
            matched_risks += 1

            gt_entity = Entity(gt_risk.entity.lower()) if gt_risk.entity else None
            gt_intent = Intent(gt_risk.intent.lower()) if gt_risk.intent else None
            gt_timing = Timing(gt_risk.timing.lower()) if gt_risk.timing else None

            entity_pairs.append((gt_entity, pipeline_causal.entity))
            intent_pairs.append((gt_intent, pipeline_causal.intent))
            timing_pairs.append((gt_timing, pipeline_causal.timing))

    return ClassificationMetrics(
        matched_risks=matched_risks,
        axes=[
            _compute_axis_metrics("Entity", entity_pairs),
            _compute_axis_metrics("Intent", intent_pairs),
            _compute_axis_metrics("Timing", timing_pairs),
        ],
    )


def _compute_axis_metrics[T](
    axis: str,
    pairs: list[tuple[T | None, T]],
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
