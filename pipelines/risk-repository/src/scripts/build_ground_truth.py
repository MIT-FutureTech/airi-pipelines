"""Build ground-truth files for full-text screening discrimination analysis.

Emits two files sharing one schema (see `GroundTruthSet`), so the discrimination
metrics script can consume either interchangeably:

- `ground_truth_proxy.json`: the "wisdom of the crowd" of the 12 model runs from
  2026-07-05 (all 13 minus Sonnet 5, which we hold out). Each doc's `score` is the
  weighted number of models that included it (include=1, uncertain=0.5); `binary` is
  the model majority vote.
- `ground_truth_real.json`: human labels from the Full-Text Screening table. `binary`
  is the OR of the two reviewers; `score` is the reviewer-assigned `relevance_score`
  (0-10) grading how include-worthy each document is.

Run from the risk-repository directory:

    uv run --env-file=../../.env python src/scripts/build_ground_truth.py
"""

import asyncio
from pathlib import Path

from pydantic import BaseModel

from toolbox.airtable import AirtableClient, Table

BASE_ID = "app32FOUBa5WcUfEO"
TABLE = "Full-Text Screening"
OUTPUT_DIR = Path("output")

# The 12 model runs from 2026-07-05, excluding Sonnet 5 (held out as the model we score).
MODEL_RUNS: dict[str, str] = {
    "gpt-5-mini": "2026-07-05T15-36-39+0000_gpt-5-mini",
    "gpt-5-4-mini": "2026-07-05T15-43-02+0000_gpt-5-4-mini",
    "gpt-5-5": "2026-07-05T15-49-41+0000_gpt-5-5",
    "haiku-4-5": "2026-07-05T15-56-29+0000_haiku-4-5",
    "opus-4-8": "2026-07-05T16-10-56+0000_opus-4-8",
    "gemini-3-flash": "2026-07-05T14-22-50+0000",
    "gemini-3-1-flash-lite": "2026-07-05T16-41-34+0000_gemini-3-1-flash-lite",
    "gemini-3-5-flash": "2026-07-05T16-48-12+0000_gemini-3-5-flash",
    "gemini-3-1-pro": "2026-07-05T16-55-55+0000_gemini-3-1-pro",
    "deepseek-v4-flash": "2026-07-05T17-03-11+0000_deepseek-v4-flash",
    "deepseek-v4-pro": "2026-07-05T17-10-32+0000_deepseek-v4-pro",
    "sonnet-4-6": "2026-07-05T17-25-30+0000_sonnet-4-6",
}

# The binary runs count "uncertain" as a half-vote toward inclusion.
DECISION_WEIGHT = {"include": 1.0, "uncertain": 0.5, "exclude": 0.0}

# The human relevance_score column is a 0-10 grade; >= 7 coincides with an include.
RELEVANCE_MAX = 10.0
RELEVANCE_INCLUDE_THRESHOLD = 7


class GroundTruthDoc(BaseModel):
    record_id: str
    title: str
    binary: bool | None
    score: float
    score_max: float


class GroundTruthSet(BaseModel):
    source: str
    description: str
    documents: list[GroundTruthDoc]


class _DecisionResult(BaseModel):
    decision: str


class _Review(BaseModel):
    record_id: str
    title: str | None = None
    human_include_1: str | None = None
    human_include_2: str | None = None
    relevance_score: int | None = None


def _load_decision(run_dir: Path, record_id: str) -> str | None:
    path = run_dir / "screen_full_text" / f"{record_id}.json"
    if not path.exists():
        return None
    return _DecisionResult.model_validate_json(path.read_text()).decision


def build_proxy(titles: dict[str, str]) -> GroundTruthSet:
    docs: list[GroundTruthDoc] = []
    for record_id, title in titles.items():
        weights = [
            DECISION_WEIGHT[d]
            for run_dir in MODEL_RUNS.values()
            if (d := _load_decision(OUTPUT_DIR / run_dir, record_id)) is not None
        ]
        if not weights:
            continue
        score = sum(weights)
        score_max = float(len(weights))
        docs.append(
            GroundTruthDoc(
                record_id=record_id,
                title=title,
                binary=score >= score_max / 2,
                score=score,
                score_max=score_max,
            )
        )
    return GroundTruthSet(
        source="proxy-12-model-consensus",
        description=(
            "Weighted inclusion count across 12 model runs (all 2026-07-05 models"
            " except Sonnet 5). include=1, uncertain=0.5, exclude=0."
        ),
        documents=docs,
    )


def _human_include(value: str | None) -> bool | None:
    match value:
        case "Include":
            return True
        case "Exclude":
            return False
        case _:
            return None


def build_real(reviews: list[_Review]) -> GroundTruthSet:
    docs: list[GroundTruthDoc] = []
    for review in reviews:
        decided = [
            d
            for d in (
                _human_include(review.human_include_1),
                _human_include(review.human_include_2),
            )
            if d is not None
        ]
        relevance = review.relevance_score
        if relevance is None:
            continue
        binary = any(decided) if decided else relevance >= RELEVANCE_INCLUDE_THRESHOLD
        docs.append(
            GroundTruthDoc(
                record_id=review.record_id,
                title=review.title or "(untitled)",
                binary=binary,
                score=float(relevance),
                score_max=RELEVANCE_MAX,
            )
        )
    return GroundTruthSet(
        source="human-reviewers",
        description=(
            "Full-Text Screening human labels. binary = OR of the two reviewers;"
            " score = reviewer-assigned relevance_score (0-10)."
        ),
        documents=docs,
    )


def _write(gt: GroundTruthSet, path: Path) -> None:
    path.write_text(gt.model_dump_json(indent=2))
    includes = sum(1 for d in gt.documents if d.binary)
    print(f"Wrote {len(gt.documents)} docs ({includes} include) -> {path}")


async def main() -> None:
    async with AirtableClient(timeout=30.0) as client:
        table = Table(client, base_id=BASE_ID, table_name=TABLE)
        records = await table.all(
            fields=[
                "title",
                "human_include_1",
                "human_include_2",
                "relevance_score",
            ]
        )
    reviews = [_Review.model_validate({"record_id": r.id, **r.fields}) for r in records]
    titles = {rv.record_id: rv.title or "(untitled)" for rv in reviews}

    _write(build_proxy(titles), OUTPUT_DIR / "ground_truth_proxy.json")
    _write(build_real(reviews), OUTPUT_DIR / "ground_truth_real.json")


if __name__ == "__main__":
    asyncio.run(main())
