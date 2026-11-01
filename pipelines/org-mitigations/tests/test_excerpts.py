from pathlib import Path

from org_mitigations.excerpts import Excerpt, load_excerpts, merge_passages
from org_mitigations.passages import Passage

TRAINING = (
    "Every team that builds AI systems must complete responsible AI training each year."
)
TESTING = "Before release, our Responsible AI team tests each model for bias against protected groups."
LOGGING = "Incidents involving our AI systems are logged and reviewed by the risk committee every quarter."
VENDORS = "Vendors supplying AI components must pass a security and privacy assessment before signing."


def _passage(document_id: str, offset: int, text: str) -> Passage:
    return Passage(
        passage_id=f"{document_id}_{offset}",
        document_id=document_id,
        offset=offset,
        text=text,
    )


EXCERPTS_CSV = """\
match_id,document_id,excerpt,passages,text
Example_Bank_001,Example_Bank_001,1,Example_Bank_001_120,We train staff on AI risks.
Example_Bank_002_part2,Example_Bank_002,3,Example_Bank_002_900;Example_Bank_002_1400,"Our board oversees AI.
It meets quarterly."
"""


class TestLoadExcerpts:
    def test_reads_each_row(self, tmp_path: Path) -> None:
        path = tmp_path / "excerpts.csv"
        path.write_text(EXCERPTS_CSV)

        assert load_excerpts(path) == [
            Excerpt(
                excerpt_id="Example_Bank_001_excerpt1",
                document_id="Example_Bank_001",
                text="We train staff on AI risks.",
                passage_ids=["Example_Bank_001_120"],
            ),
            Excerpt(
                excerpt_id="Example_Bank_002_part2_excerpt3",
                document_id="Example_Bank_002",
                text="Our board oversees AI.\nIt meets quarterly.",
                passage_ids=["Example_Bank_002_900", "Example_Bank_002_1400"],
            ),
        ]


class TestMergePassages:
    def test_keeps_separate_passages_apart_in_document_order(self) -> None:
        passages = [
            _passage("Example_Bank_001", 900, "Our board oversees AI."),
            _passage("Example_Bank_001", 120, "We train staff on AI risks."),
        ]

        assert merge_passages(passages) == [
            Excerpt(
                excerpt_id="Example_Bank_001_excerpt1",
                document_id="Example_Bank_001",
                text="We train staff on AI risks.",
                passage_ids=["Example_Bank_001_120"],
            ),
            Excerpt(
                excerpt_id="Example_Bank_001_excerpt2",
                document_id="Example_Bank_001",
                text="Our board oversees AI.",
                passage_ids=["Example_Bank_001_900"],
            ),
        ]

    def test_joins_passages_that_overlap(self) -> None:
        passages = [
            _passage("Example_Bank_001", 10, f"{TRAINING} {TESTING}"),
            _passage("Example_Bank_001", 95, f"{TESTING} {LOGGING}"),
            _passage("Example_Bank_001", 190, f"{LOGGING} {VENDORS}"),
        ]

        [excerpt] = merge_passages(passages)

        assert excerpt.text == f"{TRAINING} {TESTING} {LOGGING} {VENDORS}"
        assert excerpt.passage_ids == [
            "Example_Bank_001_10",
            "Example_Bank_001_95",
            "Example_Bank_001_190",
        ]

    def test_keeps_passages_apart_when_they_share_only_a_few_words(self) -> None:
        passages = [
            _passage("Example_Bank_001", 10, f"{TRAINING} We test models."),
            _passage("Example_Bank_001", 95, "We test models. We log incidents."),
        ]

        assert len(merge_passages(passages)) == 2

    def test_absorbs_a_passage_inside_the_one_before(self) -> None:
        passages = [
            _passage("Example_Bank_001", 10, "We train staff. We test models."),
            _passage("Example_Bank_001", 20, "staff. We test"),
        ]

        [excerpt] = merge_passages(passages)

        assert excerpt.text == "We train staff. We test models."
        assert excerpt.passage_ids == ["Example_Bank_001_10", "Example_Bank_001_20"]

    def test_never_joins_passages_from_different_documents(self) -> None:
        passages = [
            _passage("Example_Bank_002", 10, "We test models. We audit vendors."),
            _passage("Example_Bank_001", 10, "We train staff. We test models."),
        ]

        assert [excerpt.excerpt_id for excerpt in merge_passages(passages)] == [
            "Example_Bank_001_excerpt1",
            "Example_Bank_002_excerpt1",
        ]
