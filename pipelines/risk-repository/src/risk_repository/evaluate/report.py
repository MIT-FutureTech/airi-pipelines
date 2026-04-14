from risk_repository.evaluate.classify import ClassificationMetrics
from risk_repository.evaluate.extract import ExtractionMetrics
from risk_repository.evaluate.screen import ScreeningMetrics


def print_report(
    screening: ScreeningMetrics,
    extraction: ExtractionMetrics,
    classification: ClassificationMetrics,
) -> None:
    _print_screening(screening)
    print()
    _print_extraction(extraction)
    print()
    _print_classification(classification)


def _print_screening(m: ScreeningMetrics) -> None:
    print("=== Screening ===")
    print(f"Ground truth documents:  {m.gt_document_count}")
    print(f"Pipeline results:        {m.evaluated_count}")
    print(f"  Included:              {m.included_count}")
    print(f"  Uncertain:             {m.uncertain_count}")
    print(f"  Excluded:              {m.excluded_count}")
    print(f"Recall:                  {m.recall:.1%}")
    if m.false_negatives:
        print()
        print("False negatives (excluded by pipeline):")
        for doc in m.false_negatives:
            print(f"  - {doc}")


def _print_extraction(m: ExtractionMetrics) -> None:
    print("=== Extraction ===")
    print(f"Documents evaluated:     {m.documents_evaluated}")
    print(f"Ground truth risks:      {m.gt_risk_count}")
    print(f"Pipeline risks:          {m.pipeline_risk_count}")
    print(f"Matched:                 {m.matched_count}")
    print(f"Precision:               {m.precision:.1%}")
    print(f"Recall:                  {m.recall:.1%}")
    print(f"F1:                      {m.f1:.1%}")


def _print_classification(m: ClassificationMetrics) -> None:
    print("=== Classification (causal) ===")
    print(f"Matched risks evaluated: {m.matched_risks}")
    print()
    print(f"{'Axis':<16} {'Total':>6} {'Correct':>8} {'Accuracy':>9} {'Kappa':>7}")
    print(f"{'-' * 16} {'-' * 6} {'-' * 8} {'-' * 9} {'-' * 7}")
    for a in m.axes:
        print(
            f"{a.axis:<16} {a.total:>6} {a.correct:>8} {a.accuracy:>8.1%} {a.kappa:>7.3f}"
        )
