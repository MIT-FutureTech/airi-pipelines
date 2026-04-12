from risk_repository.evaluate.screen import ScreeningMetrics


def print_report(screening: ScreeningMetrics) -> None:
    _print_screening(screening)


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
