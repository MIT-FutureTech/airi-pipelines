import csv
import datetime
from pathlib import Path

import pytest

from org_mitigations.companies import Company
from org_mitigations.documents import DatePrecision, Document
from org_mitigations.evidence import Evidence
from org_mitigations.excerpts import Excerpt
from org_mitigations.search.answer import Strength
from org_mitigations.sheets.tabs import (
    EvidenceRow,
    ExcerptRow,
    evidence_rows,
    excerpt_rows,
    format_date,
    write_tab,
)
from org_mitigations.taxonomy import Code, Locus

BANK = Company(company_id="recA", name="Example Bank", sector="Finance")
RETAIL = Company(company_id="recB", name="Example Retail", sector="Trade")
INSURER = Company(company_id="recC", name="Example Insurer", sector="Finance")
TAXONOMY = [
    Locus(
        code="1",
        name="Technical & Model",
        short_name="Technical",
        definition="Mitigations to the model itself.",
        codes=[
            Code(
                code="1.1",
                name="Interpretability & Transparency",
                short_name="Interpretability",
                definition="Mitigations that explain a model.",
                examples=["Explainability tools"],
            ),
        ],
    ),
    Locus(
        code="2",
        name="Human & Organization",
        short_name="Organization",
        definition="Mitigations at the organizational level.",
        codes=[
            Code(
                code="2.2",
                name="Accountability & Responsibility",
                short_name="Accountability",
                definition="Mitigations that hold an organization to account.",
                examples=["Board oversight"],
            ),
        ],
    ),
]


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


def evidence(evidence_id: str, excerpt_id: str, quote: str) -> Evidence:
    mitigation_id, _ = evidence_id.rsplit(".", 1)
    document_id, code, _ = mitigation_id.split("__")
    return Evidence(
        evidence_id=evidence_id,
        mitigation_id=mitigation_id,
        document_id=document_id,
        code=code,
        mitigation="Board oversight of AI",
        reasoning="Board-level accountability for AI.",
        quote=quote,
        strength=Strength.STATED,
        excerpt_id=excerpt_id,
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


class TestEvidenceRows:
    @pytest.fixture
    def rows(self) -> list[EvidenceRow]:
        return evidence_rows(
            company_names=["Example Retail", "Example Bank"],
            taxonomy=TAXONOMY,
            companies=[BANK, RETAIL, INSURER],
            documents=[
                document("Bank_001", "recA"),
                document("Bank_002", "recA"),
                document("Retail_001", "recB"),
                document("Insurer_001", "recC"),
            ],
            excerpts=[
                excerpt("Bank_001_excerpt1", "Bank_001"),
                excerpt("Bank_002_excerpt1", "Bank_002"),
                excerpt("Retail_001_excerpt1", "Retail_001"),
                excerpt("Insurer_001_excerpt1", "Insurer_001"),
            ],
            evidence=[
                evidence("Bank_002__2.2__1.1", "Bank_002_excerpt1", "excerpt1"),
                evidence("Bank_002__2.2__1.2", "Bank_002_excerpt1", "text"),
                evidence("Bank_001__2.2__1.1", "Bank_001_excerpt1", "Our board"),
                evidence("Bank_001__1.1__1.1", "Bank_001_excerpt1", "text"),
                evidence("Retail_001__2.2__1.1", "Retail_001_excerpt1", "text"),
                evidence("Insurer_001__2.2__1.1", "Insurer_001_excerpt1", "text"),
            ],
        )

    def test_lists_the_named_companies_by_code_then_document(
        self, rows: list[EvidenceRow]
    ) -> None:
        evidence_ids = [row.evidence_id for row in rows]

        assert evidence_ids == [
            "Retail_001__2.2__1.1",
            "Bank_001__1.1__1.1",
            "Bank_001__2.2__1.1",
            "Bank_002__2.2__1.1",
            "Bank_002__2.2__1.2",
        ]

    def test_describes_each_quote(self, rows: list[EvidenceRow]) -> None:
        assert rows[0] == EvidenceRow(
            evidence_id="Retail_001__2.2__1.1",
            mitigation_id="Retail_001__2.2__1",
            company="Example Retail",
            document_id="Retail_001",
            excerpt_id="Retail_001_excerpt1",
            code="2.2",
            code_name="Accountability & Responsibility",
            mitigation="Board oversight of AI",
            strength=Strength.STATED,
            quote="text",
            quote_start=20,
            quote_end=24,
            reasoning="Board-level accountability for AI.",
        )

    def test_leaves_the_position_of_an_unlocated_quote_blank(
        self, rows: list[EvidenceRow]
    ) -> None:
        unlocated = next(row for row in rows if row.quote == "Our board")

        assert (unlocated.quote_start, unlocated.quote_end) == (None, None)


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
