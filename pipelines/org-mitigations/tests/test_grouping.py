from org_mitigations.excerpts import Excerpt
from org_mitigations.grouping import group_excerpts


def _excerpts(document_id: str, *sizes: int) -> list[Excerpt]:
    return [
        Excerpt(
            excerpt_id=f"{document_id}_excerpt{number}",
            document_id=document_id,
            text="x" * size,
            passage_ids=[f"{document_id}_{number}"],
        )
        for number, size in enumerate(sizes, start=1)
    ]


def _ids(groups: list[list[Excerpt]]) -> list[list[str]]:
    return [[excerpt.excerpt_id for excerpt in group] for group in groups]


class TestGroupExcerpts:
    def test_keeps_documents_together_while_they_fit(self) -> None:
        excerpts = _excerpts("Doc_001", 20, 20) + _excerpts("Doc_002", 30)

        assert _ids(group_excerpts(excerpts, max_chars=100)) == [
            ["Doc_001_excerpt1", "Doc_001_excerpt2", "Doc_002_excerpt1"],
        ]

    def test_starts_a_new_group_rather_than_split_a_document_that_fits(
        self,
    ) -> None:
        excerpts = (
            _excerpts("Doc_001", 50)
            + _excerpts("Doc_002", 30, 30)
            + _excerpts("Doc_003", 30)
        )

        assert _ids(group_excerpts(excerpts, max_chars=100)) == [
            ["Doc_001_excerpt1"],
            ["Doc_002_excerpt1", "Doc_002_excerpt2", "Doc_003_excerpt1"],
        ]

    def test_splits_a_document_over_the_limit_into_even_pieces(self) -> None:
        excerpts = _excerpts("Doc_001", 30, 30, 30, 30, 30, 30)

        assert _ids(group_excerpts(excerpts, max_chars=100)) == [
            ["Doc_001_excerpt1", "Doc_001_excerpt2", "Doc_001_excerpt3"],
            ["Doc_001_excerpt4", "Doc_001_excerpt5", "Doc_001_excerpt6"],
        ]

    def test_fills_the_last_piece_of_a_document_with_the_next_document(
        self,
    ) -> None:
        excerpts = _excerpts("Doc_001", 30, 30, 30, 30, 30, 30) + _excerpts(
            "Doc_002", 10
        )

        assert _ids(group_excerpts(excerpts, max_chars=100)) == [
            ["Doc_001_excerpt1", "Doc_001_excerpt2", "Doc_001_excerpt3"],
            [
                "Doc_001_excerpt4",
                "Doc_001_excerpt5",
                "Doc_001_excerpt6",
                "Doc_002_excerpt1",
            ],
        ]

    def test_has_no_groups_without_excerpts(self) -> None:
        assert group_excerpts([], max_chars=100) == []
