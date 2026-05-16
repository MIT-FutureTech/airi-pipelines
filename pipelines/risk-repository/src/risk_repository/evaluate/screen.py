from collections.abc import Sequence
from pathlib import Path

from pydantic import BaseModel

from risk_repository.evaluate.ground_truth import GroundTruthDocument
from risk_repository.results import PipelineStage, load, result_path
from risk_repository.screen import Decision, ScreeningResult


def is_positive_pipeline(decision: Decision) -> bool:
    return decision in {Decision.INCLUDE, Decision.UNCERTAIN}


def is_positive_ground_truth(decision: Decision) -> bool:
    return decision == Decision.INCLUDE


def _latest_screening_result(results_dir: Path, readable_id: str) -> Path | None:
    for stage in (PipelineStage.SCREEN_FULL_TEXT, PipelineStage.SCREEN_ABSTRACT):
        path = result_path(results_dir, stage, readable_id)
        if path.exists():
            return path
    return None


class DecisionCounts(BaseModel):
    include: int = 0
    exclude: int = 0
    uncertain: int = 0

    @property
    def total(self) -> int:
        return self.include + self.exclude + self.uncertain


class ScreeningMetrics(BaseModel):
    gt_counts: DecisionCounts
    pipeline_counts: DecisionCounts
    evaluated_count: int
    true_positives: int
    false_positives: int
    true_negatives: int
    false_negatives: int
    precision: float
    recall: float
    f2: float
    false_positive_refs: list[str]
    false_negative_refs: list[str]


def evaluate_screening(
    ground_truth_docs: Sequence[GroundTruthDocument],
    results_dir: Path,
) -> ScreeningMetrics:
    gt_counts = DecisionCounts()
    pipeline_counts = DecisionCounts()
    tp = 0
    fp = 0
    tn = 0
    fn = 0
    false_positive_refs: list[str] = []
    false_negative_refs: list[str] = []

    for gt_doc in ground_truth_docs:
        if gt_doc.screening_result is None:
            continue
        path = _latest_screening_result(results_dir, gt_doc.readable_id)
        if path is None:
            continue

        gt_decision = gt_doc.screening_result
        pipeline_decision = load(path, ScreeningResult).decision

        match gt_decision:
            case Decision.INCLUDE:
                gt_counts.include += 1
            case Decision.EXCLUDE:
                gt_counts.exclude += 1
            case Decision.UNCERTAIN:
                gt_counts.uncertain += 1

        match pipeline_decision:
            case Decision.INCLUDE:
                pipeline_counts.include += 1
            case Decision.EXCLUDE:
                pipeline_counts.exclude += 1
            case Decision.UNCERTAIN:
                pipeline_counts.uncertain += 1

        gt_positive = is_positive_ground_truth(gt_decision)
        pred_positive = is_positive_pipeline(pipeline_decision)

        if pred_positive and gt_positive:
            tp += 1
        elif pred_positive and not gt_positive:
            fp += 1
            false_positive_refs.append(gt_doc.readable_id)
        elif not pred_positive and gt_positive:
            fn += 1
            false_negative_refs.append(gt_doc.readable_id)
        else:
            tn += 1

    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    # Use F-score with beta = 2 since recall is more important than precision.
    # https://en.wikipedia.org/wiki/F-score#F%CE%B2_score
    f2 = (
        5 * precision * recall / (4 * precision + recall)
        if (precision + recall) > 0
        else 0.0
    )

    return ScreeningMetrics(
        gt_counts=gt_counts,
        pipeline_counts=pipeline_counts,
        evaluated_count=gt_counts.total,
        true_positives=tp,
        false_positives=fp,
        true_negatives=tn,
        false_negatives=fn,
        precision=precision,
        recall=recall,
        f2=f2,
        false_positive_refs=sorted(false_positive_refs),
        false_negative_refs=sorted(false_negative_refs),
    )
