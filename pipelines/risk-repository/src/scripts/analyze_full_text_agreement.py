"""Summarize human vs. LLM agreement on the Full-Text Screening table.

One-off analysis for a team check-in. Pulls every record from the
`Full-Text Screening` Airtable table and reports include rates, inter-reviewer
agreement, and the human/LLM confusion matrix, plus the human exclusion reasons
behind the cases where the pipeline and the reviewers disagree.

Run with:

    uv run --env-file=.env python \
        pipelines/risk-repository/src/scripts/analyze_full_text_agreement.py
"""

import asyncio
from collections import Counter

from pydantic import BaseModel, Field

from toolbox.airtable import AirtableClient, Table

BASE_ID = "app32FOUBa5WcUfEO"
TABLE_NAME = "Full-Text Screening"
AIRTABLE_TIMEOUT = 30.0

FIELDS = [
    "title",
    "human_include_1",
    "human_include_2",
    "human_reason_1",
    "human_reason_2",
    "review_status_1",
    "review_status_2",
    "llm_include",
    "llm_reasoning",
    "screening_status",
    "text_source",
]


class FullTextRow(BaseModel):
    record_id: str
    title: str | None = None
    human_include_1: str | None = None
    human_include_2: str | None = None
    human_reason_1: list[str] = Field(default_factory=list)
    human_reason_2: list[str] = Field(default_factory=list)
    review_status_1: str | None = None
    review_status_2: str | None = None
    llm_include: str | None = None
    llm_reasoning: str | None = None
    screening_status: str | None = None
    text_source: str | None = None


def normalize_human(value: str | None) -> str | None:
    """Map a human single-select to include/exclude, or None if undecided."""
    match value:
        case "Include":
            return "include"
        case "Exclude":
            return "exclude"
        case _:
            return None


def human_consensus(row: FullTextRow) -> str | None:
    """Combine the two reviewers into one human label.

    Returns include/exclude when the deciding reviewers agree (or only one has
    decided), "conflict" when they disagree, or None when neither has decided.
    """
    decisions = [
        d
        for d in (
            normalize_human(row.human_include_1),
            normalize_human(row.human_include_2),
        )
        if d is not None
    ]
    if not decisions:
        return None
    if len(set(decisions)) == 1:
        return decisions[0]
    return "conflict"


def pct(numerator: int, denominator: int) -> str:
    if denominator == 0:
        return "n/a"
    return f"{100 * numerator / denominator:.0f}% ({numerator}/{denominator})"


def cohens_kappa(both: list[tuple[str, str]]) -> float | None:
    """Cohen's kappa for paired binary (include/exclude) labels."""
    n = len(both)
    if n == 0:
        return None
    observed = sum(1 for a, b in both if a == b) / n
    labels = {"include", "exclude"}
    a_counts = Counter(a for a, _ in both)
    b_counts = Counter(b for _, b in both)
    expected = sum((a_counts[x] / n) * (b_counts[x] / n) for x in labels)
    if expected == 1:
        return 1.0
    return (observed - expected) / (1 - expected)


async def fetch_rows() -> list[FullTextRow]:
    async with AirtableClient(timeout=AIRTABLE_TIMEOUT) as client:
        table = Table(client, base_id=BASE_ID, table_name=TABLE_NAME)
        records = await table.all(fields=FIELDS)
    return [
        FullTextRow.model_validate({"record_id": r.id, **r.fields}) for r in records
    ]


def report(rows: list[FullTextRow]) -> None:
    total = len(rows)
    llm_scored = [r for r in rows if normalize_llm(r.llm_include) is not None]
    reviewer1 = [r for r in rows if normalize_human(r.human_include_1) is not None]
    reviewer2 = [r for r in rows if normalize_human(r.human_include_2) is not None]
    human_any = [r for r in rows if human_consensus(r) is not None]
    human_both = [
        r
        for r in rows
        if normalize_human(r.human_include_1) is not None
        and normalize_human(r.human_include_2) is not None
    ]

    print("=" * 72)
    print("FULL-TEXT SCREENING: HUMAN vs. LLM AGREEMENT")
    print("=" * 72)
    print(f"Total records in table:           {total}")
    print(f"LLM-screened (include/exclude):   {len(llm_scored)}")
    print(f"Human-reviewed (>=1 reviewer):    {len(human_any)}")
    print(f"Double-reviewed (both reviewers): {len(human_both)}")
    text_sources = Counter(r.text_source for r in llm_scored)
    print(f"LLM text_source breakdown:        {dict(text_sources)}")
    print()

    print("-- INCLUDE RATES " + "-" * 55)
    llm_includes = sum(
        1 for r in llm_scored if normalize_llm(r.llm_include) == "include"
    )
    print(f"LLM include rate:        {pct(llm_includes, len(llm_scored))}")
    r1_inc = sum(
        1 for r in reviewer1 if normalize_human(r.human_include_1) == "include"
    )
    r2_inc = sum(
        1 for r in reviewer2 if normalize_human(r.human_include_2) == "include"
    )
    print(f"Reviewer 1 include rate: {pct(r1_inc, len(reviewer1))}")
    print(f"Reviewer 2 include rate: {pct(r2_inc, len(reviewer2))}")
    human_slots = [normalize_human(r.human_include_1) for r in reviewer1] + [
        normalize_human(r.human_include_2) for r in reviewer2
    ]
    human_inc = sum(1 for d in human_slots if d == "include")
    print(f"Human include rate (pooled reviews): {pct(human_inc, len(human_slots))}")
    print()

    print("-- HUMAN vs. HUMAN " + "-" * 53)
    paired = [
        (normalize_human(r.human_include_1), normalize_human(r.human_include_2))
        for r in human_both
    ]
    both_pairs = [(a, b) for a, b in paired if a is not None and b is not None]
    agree = sum(1 for a, b in both_pairs if a == b)
    both_inc = sum(1 for a, b in both_pairs if a == b == "include")
    both_exc = sum(1 for a, b in both_pairs if a == b == "exclude")
    disagree = len(both_pairs) - agree
    print(f"Raw agreement:    {pct(agree, len(both_pairs))}")
    print(f"  both include:   {both_inc}")
    print(f"  both exclude:   {both_exc}")
    print(f"  disagree:       {disagree}")
    kappa = cohens_kappa(both_pairs)
    if kappa is not None:
        print(f"Cohen's kappa:    {kappa:.2f}")
    print()

    print("-- HUMAN (consensus) vs. LLM " + "-" * 43)
    confusion: Counter[tuple[str, str]] = Counter()
    comparable: list[FullTextRow] = []
    for r in rows:
        human = human_consensus(r)
        llm = normalize_llm(r.llm_include)
        if human in ("include", "exclude") and llm is not None:
            confusion[(human, llm)] += 1
            comparable.append(r)
    print(f"Comparable records (human decided, LLM scored): {len(comparable)}")
    agree_hl = confusion[("include", "include")] + confusion[("exclude", "exclude")]
    print(f"Raw agreement: {pct(agree_hl, len(comparable))}")
    print()
    print("                      LLM include   LLM exclude   LLM uncertain")
    for human in ("include", "exclude"):
        cells = "   ".join(
            f"{confusion[(human, llm)]:>11}"
            for llm in ("include", "exclude", "uncertain")
        )
        print(f"  human {human:<8}  {cells}")
    print()
    over = confusion[("exclude", "include")]
    under = confusion[("include", "exclude")]
    print(f"LLM over-includes (human exclude / LLM include): {over}")
    print(f"LLM over-excludes (human include / LLM exclude): {under}")
    print()

    print("-- WHY THE PIPELINE OVER-INCLUDES " + "-" * 38)
    print("Human exclusion reasons on records the LLM marked include:")
    reason_counts: Counter[str] = Counter()
    examples: list[FullTextRow] = []
    for r in rows:
        if (
            human_consensus(r) == "exclude"
            and normalize_llm(r.llm_include) == "include"
        ):
            examples.append(r)
            for reason in (*r.human_reason_1, *r.human_reason_2):
                if reason.startswith("Excl"):
                    reason_counts[reason] += 1
    for reason, count in reason_counts.most_common():
        print(f"  {count:>3}  {reason}")
    print()
    print("Example disagreements (human exclude / LLM include):")
    for r in examples[:6]:
        title = (r.title or "(untitled)")[:88]
        reasons = sorted(
            {x for x in (*r.human_reason_1, *r.human_reason_2) if x != "Incl"}
        )
        reasoning = " ".join((r.llm_reasoning or "").split())[:240]
        print(f"  - {title}")
        print(f"      human: {'; '.join(reasons)}")
        print(f"      LLM:   {reasoning}")


def normalize_llm(value: str | None) -> str | None:
    match value:
        case "include" | "exclude" | "uncertain":
            return value
        case _:
            return None


async def main() -> None:
    rows = await fetch_rows()
    report(rows)


if __name__ == "__main__":
    asyncio.run(main())
