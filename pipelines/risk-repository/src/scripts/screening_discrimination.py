"""Discrimination metrics for a graded full-text screening run.

Given a run that emits `predicted_include_count` per document and a ground-truth file
(see build_ground_truth.py), reports how well the score ranks true includes ahead of
excludes, as a function of how far down the sorted list a reviewer reads:

- precision, recall, and NDCG plotted against a normalized stopping point (0-100%)
- the sorted ranks of the ground-truth includes, whose worst case is the fraction of
  the corpus a reviewer must read to reach 100% recall.

Ties are broken pessimistically (includes ranked behind excludes on the same score), so
the recall curve and the "reach 100%" figure are worst-case.

Run from the risk-repository directory, e.g.:

    uv run python src/scripts/screening_discrimination.py \
        --run output/2026-07-05T16-03-19+0000_sonnet-5 \
        --ground-truth output/ground_truth_real.json
"""

# matplotlib's type stubs are partial, so its calls trip reportUnknownMemberType.
# pyright: reportUnknownMemberType=false

import argparse
import csv
from collections import Counter
from math import log2
from pathlib import Path

import matplotlib.pyplot as plt
from pydantic import BaseModel


class GroundTruthDoc(BaseModel):
    record_id: str
    title: str
    binary: bool | None
    score: float
    score_max: float


class ScoredDoc(BaseModel):
    record_id: str
    title: str
    run_score: float
    is_include: bool
    relevance: float  # graded relevance in [0, 1]


class GroundTruthSet(BaseModel):
    documents: list[GroundTruthDoc]


class _RunResult(BaseModel):
    predicted_include_count: int | None = None


def load_ground_truth(path: Path) -> dict[str, GroundTruthDoc]:
    gt = GroundTruthSet.model_validate_json(path.read_text())
    return {d.record_id: d for d in gt.documents if d.binary is not None}


def load_run_scores(path: Path) -> dict[str, float]:
    """Accept a results dir (one FullTextScreeningResult json per doc) or a
    ground-truth file (uses each doc's `score` as the run score)."""
    if path.is_dir():
        scores: dict[str, float] = {}
        for file in (path / "screen_full_text").glob("*.json"):
            result = _RunResult.model_validate_json(file.read_text())
            if result.predicted_include_count is not None:
                scores[file.stem] = float(result.predicted_include_count)
        return scores
    gt = GroundTruthSet.model_validate_json(path.read_text())
    return {d.record_id: d.score for d in gt.documents}


def join(
    run_scores: dict[str, float], ground_truth: dict[str, GroundTruthDoc]
) -> list[ScoredDoc]:
    joined: list[ScoredDoc] = []
    for record_id, gt in ground_truth.items():
        if record_id not in run_scores:
            continue
        joined.append(
            ScoredDoc(
                record_id=record_id,
                title=gt.title,
                run_score=run_scores[record_id],
                is_include=bool(gt.binary),
                relevance=gt.score / gt.score_max if gt.score_max else 0.0,
            )
        )
    # Descending score; pessimistic tie-break puts includes behind excludes.
    joined.sort(key=lambda d: (-d.run_score, d.is_include))
    return joined


def dcg(relevances: list[float]) -> float:
    return sum(rel / log2(rank + 1) for rank, rel in enumerate(relevances, start=1))


class CurvePoint(BaseModel):
    k: int
    pct: float
    precision: float
    recall: float
    ndcg: float


def build_curve(ranked: list[ScoredDoc]) -> list[CurvePoint]:
    n = len(ranked)
    total_includes = sum(d.is_include for d in ranked)
    ideal_rel = sorted((d.relevance for d in ranked), reverse=True)
    run_rel = [d.relevance for d in ranked]
    curve: list[CurvePoint] = []
    hits = 0
    for k in range(1, n + 1):
        if ranked[k - 1].is_include:
            hits += 1
        idcg = dcg(ideal_rel[:k])
        curve.append(
            CurvePoint(
                k=k,
                pct=100 * k / n,
                precision=hits / k,
                recall=hits / total_includes if total_includes else 0.0,
                ndcg=dcg(run_rel[:k]) / idcg if idcg else 0.0,
            )
        )
    return curve


def plot(ranked: list[ScoredDoc], curve: list[CurvePoint], run: str) -> None:
    n = len(ranked)
    pct = [p.pct for p in curve]
    include_pcts = [
        100 * rank / n for rank, d in enumerate(ranked, start=1) if d.is_include
    ]

    _, ax = plt.subplots(figsize=(9, 5))
    ax.plot(pct, [p.precision for p in curve], label="precision")
    ax.plot(pct, [p.recall for p in curve], label="recall")
    ax.plot(pct, [p.ndcg for p in curve], label="NDCG")
    for x in include_pcts:
        ax.axvline(x, color="gray", alpha=0.5, zorder=0)
    if include_pcts:
        worst = max(include_pcts)
        ax.axvline(worst, color="crimson", ls="--", label=f"100% recall @ {worst:.0f}%")
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 1.02)
    ax.set_xlabel("stopping point (% of corpus read, sorted by score descending)")
    ax.set_ylabel("metric")
    ax.set_title(f"Screening discrimination — {run}")
    ax.grid(True, alpha=0.3)
    ax.legend(loc="center right")
    plt.show()


def report(ranked: list[ScoredDoc], curve: list[CurvePoint], run: str) -> None:
    n = len(ranked)
    includes = [i for i, d in enumerate(ranked, start=1) if d.is_include]
    total = len(includes)
    print("=" * 72)
    print(f"SCREENING DISCRIMINATION  ({run})")
    print("=" * 72)
    print(f"Documents scored & labeled: {n}    ground-truth includes: {total}")
    print(f"Overall NDCG (@100%): {curve[-1].ndcg:.3f}\n")

    print("Pipeline score distribution (papers assigned each score):")
    counts = Counter(d.run_score for d in ranked)
    include_counts = Counter(d.run_score for d in ranked if d.is_include)
    for score in sorted(counts, reverse=True):
        includes_here = include_counts.get(score, 0)
        note = f"   ({includes_here} include)" if includes_here else ""
        print(f"  score {score:>4g}: {counts[score]:>3} papers{note}")
    print()

    print("Ground-truth include ranks (pessimistic, 1 = top of list):")
    for rank in includes:
        d = ranked[rank - 1]
        print(f"  #{rank:>3} / {n}  (score {d.run_score:g})  {d.title[:70]}")
    if includes:
        worst = max(includes)
        best = min(includes)
        print(
            f"\nTo reach 100% recall: read {worst}/{n} docs = {100 * worst / n:.0f}% "
            + f"of the corpus (best include at #{best})"
        )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", type=Path, required=True)
    parser.add_argument("--ground-truth", type=Path, required=True)
    parser.add_argument("--csv", type=Path, default=None)
    args = parser.parse_args()

    ground_truth = load_ground_truth(args.ground_truth)
    run_scores = load_run_scores(args.run)
    ranked = join(run_scores, ground_truth)
    if not ranked:
        raise SystemExit("No overlap between run scores and ground truth.")
    missing = len(ground_truth) - len(ranked)
    if missing:
        print(f"[note] {missing} labeled docs had no score in the run; excluded.\n")

    curve = build_curve(ranked)
    report(ranked, curve, args.run.name)
    plot(ranked, curve, args.run.name)

    if args.csv:
        with args.csv.open("w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["k", "pct", "precision", "recall", "ndcg"])
            for p in curve:
                writer.writerow(
                    [
                        p.k,
                        f"{p.pct:.2f}",
                        f"{p.precision:.4f}",
                        f"{p.recall:.4f}",
                        f"{p.ndcg:.4f}",
                    ]
                )
        print(f"\nWrote curve -> {args.csv}")
    if plt.isinteractive():
        breakpoint()


if __name__ == "__main__":
    main()
