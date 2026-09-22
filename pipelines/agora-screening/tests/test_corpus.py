import csv
from pathlib import Path

import pytest

from agora_screening.corpus import (
    DocumentRecord,
    apply_selection,
    load_oecd_corpus,
    oecd_slug,
    select_with_text,
)

_COLUMNS = [
    "Aggregator Link",
    "Aggregator Summary",
    "Link",
    "Name",
    "Jurisdiction",
    "Organization",
    "Date introduced",
    "Most recent activity",
    "Most recent activity date",
    "Category",
    "Initiative type",
    "Binding",
    "ID",
    "Text",
]


def _write_corpus(path: Path, rows: list[dict[str, str]]) -> Path:
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=_COLUMNS)
        writer.writeheader()
        for row in rows:
            writer.writerow({column: row.get(column, "") for column in _COLUMNS})
    return path


def _row(readable_id: str, text: str, name: str = "An initiative") -> dict[str, str]:
    return {
        "ID": readable_id,
        "Text": text,
        "Name": name,
        "Aggregator Link": f"https://oecd.ai/en/dashboards/policy-initiatives/{readable_id.lower()}",
    }


@pytest.fixture
def corpus_path(tmp_path: Path) -> Path:
    return _write_corpus(
        tmp_path / "corpus.csv",
        [
            _row("ID_0001", ""),
            _row("ID_0002", "x" * 500),
            _row("ID_0003", "short"),
            _row("ID_0004", "y" * 500),
        ],
    )


def test_oecd_slug_takes_the_trailing_segment() -> None:
    assert oecd_slug(
        "https://oecd.ai/en/dashboards/policy-initiatives/ai-for-business/"
    ) == ("ai-for-business")


def test_load_numbers_every_row_including_textless_ones(corpus_path: Path) -> None:
    records = load_oecd_corpus(corpus_path)
    assert [record.readable_id for record in records] == [
        "ID_0001",
        "ID_0002",
        "ID_0003",
        "ID_0004",
    ]
    assert [record.csv_row for record in records] == [1, 2, 3, 4]


def test_select_with_text_keeps_only_usable_documents(corpus_path: Path) -> None:
    selected = select_with_text(load_oecd_corpus(corpus_path), min_chars=200)
    assert [record.readable_id for record in selected] == ["ID_0002", "ID_0004"]


def test_select_with_text_numbers_survivors_contiguously(corpus_path: Path) -> None:
    selected = select_with_text(load_oecd_corpus(corpus_path), min_chars=200)
    assert [record.text_row for record in selected] == [1, 2]
    assert [record.csv_row for record in selected] == [2, 4]


def test_selection_by_id(corpus_path: Path) -> None:
    records = select_with_text(load_oecd_corpus(corpus_path), min_chars=200)
    selected = apply_selection(records, document_ids=["ID_0004"], limit=None)
    assert [record.readable_id for record in selected] == ["ID_0004"]


def test_selection_warns_about_unknown_ids(
    corpus_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    records = select_with_text(load_oecd_corpus(corpus_path), min_chars=200)
    selected = apply_selection(records, document_ids=["ID_9999"], limit=None)
    assert selected == []
    assert "ID_9999" in caplog.text


def test_limit_applies_after_id_filtering(corpus_path: Path) -> None:
    records = select_with_text(load_oecd_corpus(corpus_path), min_chars=200)
    selected = apply_selection(records, document_ids=None, limit=1)
    assert [record.readable_id for record in selected] == ["ID_0002"]


def test_records_are_immutable(corpus_path: Path) -> None:
    record: DocumentRecord = load_oecd_corpus(corpus_path)[0]
    with pytest.raises(ValueError, match="frozen"):
        record.text = "mutated"  # pyright: ignore[reportAttributeAccessIssue]
