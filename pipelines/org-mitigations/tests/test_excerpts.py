from pathlib import Path

from org_mitigations.excerpts import Excerpt, load_excerpts

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
