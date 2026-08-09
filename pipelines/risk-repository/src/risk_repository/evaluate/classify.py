import logging
from collections import Counter
from collections.abc import Sequence
from pathlib import Path

from pydantic import BaseModel

from risk_repository.classify import (
    ClassificationResult,
    ClassifiedRisk,
    Entity,
    Evidence,
    Intent,
    RiskContent,
    RiskNode,
    Subdomain,
    Timing,
    category_nodes,
)
from risk_repository.evaluate.ground_truth import CategoryLevel, GroundTruthRisk
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


def ground_truth_nodes(risk: GroundTruthRisk) -> tuple[RiskNode, ...]:
    """Read a previous-iteration risk as a node chain, keyed by its Ev_ID."""
    if risk.level is CategoryLevel.SUBCATEGORY and risk.subcategory:
        name = risk.subcategory
        category = risk.category
    else:
        name = risk.category
        category = ""
    return category_nodes(
        RiskContent(
            name=name,
            description=risk.description,
            supporting_quote=risk.quote or "",
            additional_evidence=tuple(
                Evidence(text=text, quote="") for text in risk.additional_evidence
            ),
        ),
        risk_id=risk.ev_id,
        category=category,
    )


class Labels(BaseModel, frozen=True):
    entity: Entity | None
    intent: Intent | None
    timing: Timing | None
    subdomain: str | None

    @property
    def domain(self) -> str | None:
        return _domain_code(self.subdomain)


def ground_truth_labels(risk: GroundTruthRisk) -> Labels:
    return Labels(
        entity=Entity(risk.entity.lower()) if risk.entity else None,
        intent=Intent(risk.intent.lower()) if risk.intent else None,
        timing=Timing(risk.timing.lower()) if risk.timing else None,
        subdomain=risk.subdomain_code,
    )


def predicted_labels(classified: ClassifiedRisk) -> Labels:
    return Labels(
        entity=classified.causal.entity,
        intent=classified.causal.intent,
        timing=classified.causal.timing,
        subdomain=_subdomain_code(classified.domain.subdomain),
    )


def score_classifications(
    pairs: Sequence[tuple[GroundTruthRisk, ClassifiedRisk]],
) -> list[AxisMetrics]:
    """Score predicted labels against ground-truth labels, one metric per axis."""
    labelled = [
        (ground_truth_labels(gt_risk), predicted_labels(predicted))
        for gt_risk, predicted in pairs
    ]
    return [
        _compute_axis_metrics("Entity", [(g.entity, p.entity) for g, p in labelled]),
        _compute_axis_metrics("Intent", [(g.intent, p.intent) for g, p in labelled]),
        _compute_axis_metrics("Timing", [(g.timing, p.timing) for g, p in labelled]),
        _compute_axis_metrics("Domain", [(g.domain, p.domain) for g, p in labelled]),
        _compute_axis_metrics(
            "Subdomain", [(g.subdomain, p.subdomain) for g, p in labelled]
        ),
    ]


def evaluate_classification(
    match_results: list[DocumentMatchResult],
    results_dir: Path,
) -> ClassificationMetrics:
    pairs: list[tuple[GroundTruthRisk, ClassifiedRisk]] = []

    for doc in match_results:
        classification_path = result_path(
            results_dir, PipelineStage.CLASSIFY, doc.readable_id
        )
        if not classification_path.exists():
            continue
        classification = load(classification_path, ClassificationResult)

        for match in doc.matches:
            if match.pipeline_index >= len(classification.risks):
                logger.warning(
                    f"{doc.readable_id}: pipeline index {match.pipeline_index} out of range for classification results"
                )
                continue
            pairs.append(
                (
                    doc.gt_risks[match.gt_index],
                    classification.risks[match.pipeline_index],
                )
            )

    return ClassificationMetrics(
        matched_risks=len(pairs),
        axes=score_classifications(pairs),
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
