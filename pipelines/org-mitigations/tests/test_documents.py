import datetime
from pathlib import Path

from org_mitigations.documents import DatePrecision, Document, load_documents

DOCUMENTS_CSV = """\
document_record_id,document_id,company_id,status,doc_type,title,date,date_precision,link
recD1,Example_Bank_001,recA,Validated,Annual report,2025 Annual Report,2025-01-01,year,https://example.com/ar.pdf
recD2,Example_Bank_002,recA,Validated,AI overview & principles,Our AI Principles,,,https://example.com/ai
"""


class TestLoadDocuments:
    def test_reads_each_row(self, tmp_path: Path) -> None:
        (tmp_path / "documents.csv").write_text(DOCUMENTS_CSV)

        assert load_documents(tmp_path) == [
            Document(
                document_id="Example_Bank_001",
                company_id="recA",
                title="2025 Annual Report",
                doc_type="Annual report",
                date=datetime.date(2025, 1, 1),
                date_precision=DatePrecision.YEAR,
                link="https://example.com/ar.pdf",
            ),
            Document(
                document_id="Example_Bank_002",
                company_id="recA",
                title="Our AI Principles",
                doc_type="AI overview & principles",
                date=None,
                date_precision=None,
                link="https://example.com/ai",
            ),
        ]
