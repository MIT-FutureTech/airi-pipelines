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


def _pct(count: int, total: int) -> str:
    return f"{count / total:.0%}" if total > 0 else "-"


def _print_screening(m: ScreeningMetrics) -> None:
    print("=== Screening ===")
    gt, pl = m.gt_counts, m.pipeline_counts
    print(f"              {'GT':^10}    {'Pipeline':^10}")
    print(
        f"Include:      {gt.include:>3} ({_pct(gt.include, gt.total):>4})    {pl.include:>3} ({_pct(pl.include, pl.total):>4})"
    )
    print(
        f"Uncertain:    {gt.uncertain:>3} ({_pct(gt.uncertain, gt.total):>4})    {pl.uncertain:>3} ({_pct(pl.uncertain, pl.total):>4})"
    )
    print(
        f"Exclude:      {gt.exclude:>3} ({_pct(gt.exclude, gt.total):>4})    {pl.exclude:>3} ({_pct(pl.exclude, pl.total):>4})"
    )
    print(f"Total:        {gt.total:>3}           {pl.total:>3}")
    print()
    print(f"Precision:    {m.precision:.1%}")
    print(f"Recall:       {m.recall:.1%}")
    print(f"F2:           {m.f2:.1%}")

    list_limit = 9
    if m.false_negative_refs:
        print()
        print("False negatives (excluded by pipeline, should be included):")
        for i, doc in enumerate(m.false_negative_refs):
            if i >= list_limit:
                print(f"And {len(m.false_negative_refs) - i} more")
                break
            print(f"  - {doc}")
    if m.false_positive_refs:
        print()
        print("False positives (included by pipeline, should be excluded):")
        for i, doc in enumerate(m.false_positive_refs):
            if i >= list_limit:
                print(f"And {len(m.false_positive_refs) - i} more")
                break
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
