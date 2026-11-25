from pathlib import Path

import pytest

from org_mitigations.passages import Passage, load_passages

DOCUMENTS_CSV = """\
document_record_id,document_id,company_id,doc_type,title
recD1,Example_Bank_001,recA,Annual report,2025 Annual Report
recD2,Example_Bank_002,recA,AI governance,Our Approach to AI
"""


def _write_export(export_dir: Path, passages: list[tuple[str, str, str]]) -> None:
    (export_dir / "documents.csv").write_text(DOCUMENTS_CSV)
    lines = ["passage_id,document_record_id,keyword,text"]
    lines += [
        f'{passage_id},{record_id},AI,"{text}"'
        for passage_id, record_id, text in passages
    ]
    (export_dir / "passages.csv").write_text("\n".join(lines) + "\n")


class TestLoadPassages:
    def test_reads_each_row(self, tmp_path: Path) -> None:
        _write_export(
            tmp_path,
            [
                ("Example_Bank_001_120", "recD1", "We test models for bias."),
                ("Example_Bank_002_45", "recD2", "Staff complete AI training."),
            ],
        )

        assert load_passages(tmp_path) == [
            Passage(
                passage_id="Example_Bank_001_120",
                document_id="Example_Bank_001",
                offset=120,
                text="We test models for bias.",
            ),
            Passage(
                passage_id="Example_Bank_002_45",
                document_id="Example_Bank_002",
                offset=45,
                text="Staff complete AI training.",
            ),
        ]

    def test_takes_the_document_from_the_record_not_the_passage_id(
        self, tmp_path: Path
    ) -> None:
        _write_export(tmp_path, [("Example_Bank_001_7", "recD2", "Text.")])

        assert load_passages(tmp_path)[0].document_id == "Example_Bank_002"

    def test_removes_cut_markers_at_either_end(self, tmp_path: Path) -> None:
        _write_export(
            tmp_path,
            [("Example_Bank_001_1", "recD1", " [...] Start [...] end. [...] ")],
        )

        assert load_passages(tmp_path)[0].text == "Start [...] end."

    def test_removes_control_characters_but_keeps_line_breaks(
        self, tmp_path: Path
    ) -> None:
        _write_export(tmp_path, [("Example_Bank_001_1", "recD1", "AI\x0cmodels\nare")])

        assert load_passages(tmp_path)[0].text == "AImodels\nare"

    def test_rejects_a_passage_id_without_an_offset(self, tmp_path: Path) -> None:
        _write_export(tmp_path, [("Example_Bank_001_x", "recD1", "Text.")])

        with pytest.raises(ValueError, match="invalid literal for int"):
            load_passages(tmp_path)
