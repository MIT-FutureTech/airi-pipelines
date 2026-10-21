import csv
import datetime
from pathlib import Path

import pytest

from org_mitigations.companies import Company
from org_mitigations.documents import DatePrecision, Document
from org_mitigations.excerpts import Excerpt
from org_mitigations.sheets.tabs import (
    ExcerptRow,
    excerpt_rows,
    format_date,
    write_tab,
)

BANK = Company(company_id="recA", name="Example Bank", sector="Finance")
RETAIL = Company(company_id="recB", name="Example Retail", sector="Trade")
INSURER = Company(company_id="recC", name="Example Insurer", sector="Finance")


def document(
    document_id: str,
    company_id: str,
    date: datetime.date | None = None,
    date_precision: DatePrecision | None = None,
) -> Document:
    return Document(
        document_id=document_id,
        company_id=company_id,
        title=f"{document_id} title",
        doc_type="Annual report",
        date=date,
        date_precision=date_precision,
        link=f"https://example.com/{document_id}.pdf",
    )


def excerpt(excerpt_id: str, document_id: str) -> Excerpt:
    return Excerpt(
        excerpt_id=excerpt_id,
        document_id=document_id,
        text=f"{excerpt_id} text",
        passage_ids=[f"{document_id}_100", f"{document_id}_900"],
    )


class TestFormatDate:
    @pytest.mark.parametrize(
        ("precision", "expected"),
        [
            (DatePrecision.DAY, "2025-04-29"),
            (DatePrecision.MONTH, "2025-04"),
            (DatePrecision.YEAR, "2025"),
        ],
    )
    def test_writes_the_date_to_its_precision(
        self, precision: DatePrecision, expected: str
    ) -> None:
        dated = document("Bank_001", "recA", datetime.date(2025, 4, 29), precision)

        assert format_date(dated) == expected

    def test_leaves_an_undated_document_blank(self) -> None:
        assert format_date(document("Bank_001", "recA")) == ""


class TestExcerptRows:
    @pytest.fixture
    def rows(self) -> list[ExcerptRow]:
        return excerpt_rows(
            company_names=["Example Retail", "Example Bank"],
            companies=[BANK, RETAIL, INSURER],
            documents=[
                document("Bank_002", "recA"),
                document("Bank_001", "recA"),
                document("Retail_001", "recB"),
                document("Insurer_001", "recC"),
            ],
            excerpts=[
                excerpt("Bank_001_excerpt1", "Bank_001"),
                excerpt("Bank_002_part1_excerpt1", "Bank_002"),
                excerpt("Bank_002_part2_excerpt1", "Bank_002"),
                excerpt("Retail_001_excerpt1", "Retail_001"),
                excerpt("Insurer_001_excerpt1", "Insurer_001"),
            ],
        )

    def test_lists_the_named_companies_in_order(self, rows: list[ExcerptRow]) -> None:
        excerpt_ids = [row.excerpt_id for row in rows]

        assert excerpt_ids == [
            "Retail_001_excerpt1",
            "Bank_001_excerpt1",
            "Bank_002_part1_excerpt1",
            "Bank_002_part2_excerpt1",
        ]

    def test_numbers_excerpts_across_a_documents_parts(
        self, rows: list[ExcerptRow]
    ) -> None:
        orders = [
            row.order_in_document for row in rows if row.document_id == "Bank_002"
        ]

        assert orders == [1, 2]

    def test_describes_each_excerpt(self, rows: list[ExcerptRow]) -> None:
        assert rows[0] == ExcerptRow(
            excerpt_id="Retail_001_excerpt1",
            company="Example Retail",
            document_id="Retail_001",
            document_title="Retail_001 title",
            document_type="Annual report",
            document_date="",
            document_link="https://example.com/Retail_001.pdf",
            order_in_document=1,
            passage_ids="Retail_001_100;Retail_001_900",
            text="Retail_001_excerpt1 text",
        )

    def test_rejects_an_unknown_company(self) -> None:
        with pytest.raises(KeyError, match="Example Airline"):
            excerpt_rows(
                company_names=["Example Airline"],
                companies=[BANK],
                documents=[],
                excerpts=[],
            )


class TestWriteTab:
    def test_writes_a_header_and_one_record_per_row(self, tmp_path: Path) -> None:
        path = tmp_path / "excerpts.csv"
        row = ExcerptRow(
            excerpt_id="Bank_001_excerpt1",
            company="Example Bank",
            document_id="Bank_001",
            document_title="Annual Report",
            document_type="Annual report",
            document_date="2025",
            document_link="https://example.com/ar.pdf",
            order_in_document=1,
            passage_ids="Bank_001_100",
            text="Our board oversees AI.\nIt meets quarterly.",
        )

        write_tab(path, ExcerptRow, [row])

        with path.open(encoding="utf-8", newline="") as file:
            records = list(csv.reader(file))
        assert records == [
            [
                "Excerpt ID",
                "Company",
                "Document ID",
                "Document title",
                "Document type",
                "Document date",
                "Document link",
                "Order in document",
                "Passage IDs",
                "Text",
            ],
            [
                "Bank_001_excerpt1",
                "Example Bank",
                "Bank_001",
                "Annual Report",
                "Annual report",
                "2025",
                "https://example.com/ar.pdf",
                "1",
                "Bank_001_100",
                "Our board oversees AI.\nIt meets quarterly.",
            ],
        ]
