import csv
from pathlib import Path

import pytest

from agora_screening.compare import (
    ScoredDocument,
    band,
    corrupt_extractions,
    distribution,
    invariance_groups,
    read_results,
    score_deltas,
)
from agora_screening.corpus import DocumentRecord


def _record(readable_id: str, text: str) -> DocumentRecord:
    return DocumentRecord(
        readable_id=readable_id,
        slug=readable_id.lower(),
        link="",
        aggregator_link="",
        name="",
        jurisdiction="",
        organization="",
        date_introduced="",
        most_recent_activity="",
        most_recent_activity_date="",
        category="",
        initiative_type="",
        binding="",
        summary="",
        text=text,
        csv_row=1,
    )


def _scored(readable_id: str, score: int | None) -> ScoredDocument:
    return ScoredDocument(readable_id=readable_id, score=score, title_check="yes")


@pytest.mark.parametrize(
    ("score", "expected"),
    [
        (0, "  0-9  "),
        (59, " 50-59 "),
        (60, " 60-69 "),
        (99, " 90-99 "),
        (100, " 90-99 "),
    ],
)
def test_band_labels(score: int, expected: str) -> None:
    assert band(score) == expected


def test_a_perfect_score_shares_the_top_band() -> None:
    assert distribution([_scored("ID_0001", 100), _scored("ID_0002", 95)]) == {
        " 90-99 ": 2
    }


def test_unscored_documents_are_left_out_of_the_distribution() -> None:
    assert distribution([_scored("ID_0001", 70), _scored("ID_0002", None)]) == {
        " 70-79 ": 1
    }


def test_identical_text_scoring_identically_is_not_flagged() -> None:
    corpus = [_record("ID_0001", "same text"), _record("ID_0002", "same text")]
    groups = invariance_groups([_scored("ID_0001", 70), _scored("ID_0002", 70)], corpus)
    assert len(groups) == 1
    assert groups[0].spread == 0


def test_identical_text_scoring_differently_is_flagged() -> None:
    corpus = [_record("ID_0001", "same text"), _record("ID_0002", "same text")]
    groups = invariance_groups([_scored("ID_0001", 10), _scored("ID_0002", 75)], corpus)
    assert groups[0].spread == 65
    assert sorted(groups[0].readable_ids) == ["ID_0001", "ID_0002"]


def test_documents_with_distinct_text_are_not_grouped() -> None:
    corpus = [_record("ID_0001", "one"), _record("ID_0002", "two")]
    assert (
        invariance_groups([_scored("ID_0001", 10), _scored("ID_0002", 75)], corpus)
        == []
    )


def test_unscored_documents_cannot_form_a_group() -> None:
    corpus = [_record("ID_0001", "same"), _record("ID_0002", "same")]
    assert (
        invariance_groups([_scored("ID_0001", 10), _scored("ID_0002", None)], corpus)
        == []
    )


def test_corrupt_extractions_are_reported_worst_first() -> None:
    corpus = [
        _record("ID_0001", "(cid:3)(cid:4) some real words follow here and there"),
        _record("ID_0002", "(cid:3)(cid:4)(cid:5)"),
        _record("ID_0003", "entirely clean text"),
    ]
    found = corrupt_extractions(
        [_scored("ID_0001", 75), _scored("ID_0002", 75), _scored("ID_0003", 80)],
        corpus,
        threshold=0.1,
    )
    assert [readable_id for readable_id, _, _ in found] == ["ID_0002", "ID_0001"]


def test_score_deltas_flag_a_threshold_crossing() -> None:
    deltas = score_deltas([_scored("ID_0001", 55)], [_scored("ID_0001", 65)])
    assert deltas[0].delta == -10
    assert deltas[0].crosses_threshold


def test_score_deltas_ignore_movement_within_one_side_of_the_threshold() -> None:
    deltas = score_deltas([_scored("ID_0001", 95)], [_scored("ID_0001", 65)])
    assert deltas[0].delta == 30
    assert not deltas[0].crosses_threshold


def test_documents_absent_from_the_baseline_are_skipped() -> None:
    assert score_deltas([_scored("ID_0002", 70)], [_scored("ID_0001", 70)]) == []


def test_read_results_handles_a_blank_score(tmp_path: Path) -> None:
    path = tmp_path / "results.csv"
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["ID", "Scope score", "Name (original language) found in text"],
        )
        writer.writeheader()
        writer.writerow(
            {
                "ID": "ID_0001",
                "Scope score": "85",
                "Name (original language) found in text": "yes",
            }
        )
        writer.writerow(
            {
                "ID": "ID_0002",
                "Scope score": "",
                "Name (original language) found in text": "",
            }
        )

    documents = read_results(path)
    assert [document.score for document in documents] == [85, None]
