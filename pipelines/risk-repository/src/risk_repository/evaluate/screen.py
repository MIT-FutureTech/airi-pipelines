from pathlib import Path

from pydantic import BaseModel

from risk_repository.results import PipelineStage, load, result_path
from risk_repository.screen import Decision, ScreeningResult


class ScreeningMetrics(BaseModel):
    gt_document_count: int
    evaluated_count: int
    included_count: int
    excluded_count: int
    uncertain_count: int
    recall: float
    false_negatives: list[str]


def evaluate_screening(
    gt_quick_refs: set[str],
    results_dir: Path,
) -> ScreeningMetrics:
    included = 0
    excluded = 0
    uncertain = 0
    false_negatives: list[str] = []

    for quick_ref in sorted(gt_quick_refs):
        path = result_path(results_dir, PipelineStage.SCREEN, quick_ref)
        if not path.exists():
            continue
        result = load(path, ScreeningResult)
        match result.decision:
            case Decision.INCLUDE:
                included += 1
            case Decision.EXCLUDE:
                excluded += 1
                false_negatives.append(quick_ref)
            case Decision.UNCERTAIN:
                uncertain += 1

    evaluated = included + excluded + uncertain
    recall = (included + uncertain) / evaluated if evaluated > 0 else 0.0

    return ScreeningMetrics(
        gt_document_count=len(gt_quick_refs),
        evaluated_count=evaluated,
        included_count=included,
        excluded_count=excluded,
        uncertain_count=uncertain,
        recall=recall,
        false_negatives=false_negatives,
    )
