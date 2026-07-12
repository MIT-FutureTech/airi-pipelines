from risk_repository.evaluate.classify import ClassificationMetrics
from risk_repository.evaluate.extract import (
    ExtractionMetrics,
    SideTally,
    scores,
)
from risk_repository.evaluate.screen import ScreeningMetrics


def print_report(
    screening: ScreeningMetrics | None,
    extraction: ExtractionMetrics | None,
    classification: ClassificationMetrics | None,
) -> None:
    if screening is not None:
        print_screening(screening)
        print()
    if extraction is not None:
        _print_extraction(extraction)
        print()
    if classification is not None:
        _print_classification(classification)


def _pct(count: int, total: int) -> str:
    return f"{count / total:.0%}" if total > 0 else "-"


def print_screening(m: ScreeningMetrics, *, heading: str = "Screening") -> None:
    print(f"=== {heading} ===")
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
        print(
            f"{m.false_negatives} false negatives (excluded by pipeline, should be included):"
        )
        for i, doc in enumerate(m.false_negative_refs):
            if i >= list_limit:
                print(f"And {len(m.false_negative_refs) - i} more")
                break
            print(f"  - {doc}")
    if m.false_positive_refs:
        print()
        print(
            f"{m.false_positives} false positives (included by pipeline, should be excluded):"
        )
        for i, doc in enumerate(m.false_positive_refs):
            if i >= list_limit:
                print(f"And {len(m.false_positive_refs) - i} more")
                break
            print(f"  - {doc}")


def _print_extraction(m: ExtractionMetrics) -> None:
    print("=== Extraction ===")
    print(f"Documents evaluated: {m.documents_evaluated}")
    print()
    _print_side("Ground-truth nodes", m.ground_truth, zero="missed", multi="split")
    print()
    _print_side("Pipeline nodes", m.pipeline, zero="false pos", multi="lumped")
    print()
    print("Scores (matched = mapped to exactly one counterpart)")
    print(f"{'Level':<14}{'Precision':>11}{'Recall':>9}{'F1':>8}")
    for label, gt, pipeline in (
        ("Category", m.ground_truth.category, m.pipeline.category),
        ("Subcategory", m.ground_truth.subcategory, m.pipeline.subcategory),
        ("Overall", m.ground_truth.overall, m.pipeline.overall),
    ):
        s = scores(gt, pipeline)
        print(f"{label:<14}{s.precision:>10.1%}{s.recall:>9.1%}{s.f1:>8.1%}")


def _print_side(heading: str, side: SideTally, *, zero: str, multi: str) -> None:
    print(f"{heading:<26}{'total':>7}{'matched':>9}{zero:>11}{multi:>9}")
    for label, tally in (
        ("Category", side.category),
        ("Subcategory", side.subcategory),
        ("Overall", side.overall),
    ):
        print(
            f"  {label:<24}{tally.total:>7}{tally.matched:>9}"
            + f"{tally.unmatched:>11}{tally.multi:>9}"
        )


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
