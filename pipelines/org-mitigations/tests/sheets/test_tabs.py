import csv
import datetime
import re
from pathlib import Path

import pytest

from org_mitigations.companies import Company
from org_mitigations.documents import DatePrecision, Document
from org_mitigations.domain_taxonomy import Domain, Locus
from org_mitigations.evidence import Evidence
from org_mitigations.excerpts import Excerpt
from org_mitigations.practices.answer import (
    Affiliation,
    Answer,
    Relation,
    TaggedPractice,
)
from org_mitigations.practices.calls import PracticesResult
from org_mitigations.search.answer import Strength
from org_mitigations.search.mitigations import FoundMitigation, FoundQuote
from org_mitigations.sheets.tabs import (
    AffiliationRow,
    EvidenceRow,
    ExcerptRow,
    MitigationRow,
    PracticeRow,
    affiliation_rows,
    evidence_rows,
    excerpt_rows,
    format_document_date,
    mitigation_rows,
    practice_rows,
    write_tab,
)

BANK = Company(company_id="recA", name="Example Bank", sector="Finance")
RETAIL = Company(company_id="recB", name="Example Retail", sector="Trade")
INSURER = Company(company_id="recC", name="Example Insurer", sector="Finance")
TAXONOMY = [
    Locus(
        code="1",
        name="Technical & Model",
        short_name="Technical",
        definition="Mitigations to the model itself.",
        domains=[
            Domain(
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
        domains=[
            Domain(
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
        domain_code=code,
        mitigation_name="Board oversight of AI",
        reasoning="Board-level accountability for AI.",
        quote=quote,
        strength=Strength.STATED,
        excerpt_id=excerpt_id,
    )


def found_mitigation(mitigation_id: str, company_id: str) -> FoundMitigation:
    _, code, _ = mitigation_id.split("__")
    return FoundMitigation(
        mitigation_id=mitigation_id,
        company_id=company_id,
        domain_code=code,
        name="Board oversight of AI",
        reasoning="Board-level accountability for AI.",
        quotes=[
            FoundQuote(
                excerpt_id="Bank_001_excerpt1",
                quote="Our board oversees AI.",
                strength=Strength.DESCRIBED,
            ),
            FoundQuote(
                excerpt_id="Bank_001_excerpt1",
                quote="It meets quarterly.",
                strength=Strength.STATED,
            ),
        ],
    )


def tag(
    practice: str, *subtypes: str, quote_numbers: tuple[int, ...] = (1,)
) -> TaggedPractice:
    return TaggedPractice(
        name=practice,
        subtypes=list(subtypes),
        quote_numbers=list(quote_numbers),
        reasoning=f"Fits {practice}.",
    )


def practices_result(
    mitigation_id: str,
    *tags: TaggedPractice,
    affiliations: tuple[Affiliation, ...] = (),
) -> PracticesResult:
    return PracticesResult(
        mitigation_id=mitigation_id,
        answer=Answer(
            match_id=mitigation_id,
            tagged_practices=list(tags),
            affiliations=list(affiliations),
        ),
        model="test-model",
        usage=None,
    )


class TestFormatDocumentDate:
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

        assert format_document_date(dated) == expected

    def test_leaves_an_undated_document_blank(self) -> None:
        assert format_document_date(document("Bank_001", "recA")) == ""


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
            domain_code="2.2",
            domain_name="Accountability & Responsibility",
            mitigation_name="Board oversight of AI",
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


class TestMitigationRows:
    @pytest.fixture
    def rows(self) -> list[MitigationRow]:
        return mitigation_rows(
            company_names=["Example Retail", "Example Bank"],
            taxonomy=TAXONOMY,
            companies=[BANK, RETAIL, INSURER],
            mitigations=[
                found_mitigation("Example_Bank__2.2__1", "recA"),
                found_mitigation("Example_Bank__1.1__1", "recA"),
                found_mitigation("Example_Retail__2.2__1", "recB"),
                found_mitigation("Example_Insurer__2.2__1", "recC"),
            ],
            practices_results={
                "Example_Bank__2.2__1": practices_result(
                    "Example_Bank__2.2__1",
                    tag("Named accountability for AI risk"),
                    tag("Published AI policy"),
                ),
                "Example_Bank__1.1__1": practices_result("Example_Bank__1.1__1"),
                "Example_Retail__2.2__1": practices_result(
                    "Example_Retail__2.2__1", tag("Named accountability for AI risk")
                ),
            },
        )

    def test_lists_the_named_companies_by_code(self, rows: list[MitigationRow]) -> None:
        mitigation_ids = [row.mitigation_id for row in rows]

        assert mitigation_ids == [
            "Example_Retail__2.2__1",
            "Example_Bank__1.1__1",
            "Example_Bank__2.2__1",
        ]

    def test_describes_each_mitigation(self, rows: list[MitigationRow]) -> None:
        assert rows[2] == MitigationRow(
            mitigation_id="Example_Bank__2.2__1",
            company="Example Bank",
            sector="Finance",
            domain_code="2.2",
            domain_name="Accountability & Responsibility",
            mitigation_name="Board oversight of AI",
            reasoning="Board-level accountability for AI.",
            quotes="Our board oversees AI.\n\nIt meets quarterly.",
            practices="Named accountability for AI risk; Published AI policy",
        )

    def test_leaves_an_untagged_mitigations_practices_blank(
        self, rows: list[MitigationRow]
    ) -> None:
        assert rows[1].practices == ""

    def test_rejects_a_mitigation_with_no_practices_result(self) -> None:
        with pytest.raises(ValueError, match=re.escape("Example_Bank__2.2__1")):
            mitigation_rows(
                company_names=["Example Bank"],
                taxonomy=TAXONOMY,
                companies=[BANK],
                mitigations=[found_mitigation("Example_Bank__2.2__1", "recA")],
                practices_results={},
            )


class TestPracticeRows:
    @pytest.fixture
    def rows(self) -> list[PracticeRow]:
        return practice_rows(
            company_names=["Example Retail", "Example Bank"],
            taxonomy=TAXONOMY,
            companies=[BANK, RETAIL],
            mitigations=[
                found_mitigation("Example_Bank__2.2__1", "recA"),
                found_mitigation("Example_Bank__1.1__1", "recA"),
                found_mitigation("Example_Retail__2.2__1", "recB"),
            ],
            practices_results={
                "Example_Bank__2.2__1": practices_result(
                    "Example_Bank__2.2__1",
                    tag(
                        "Named accountability for AI risk",
                        "Board of directors oversight",
                        quote_numbers=(1, 2),
                    ),
                    tag("Published AI policy", quote_numbers=(2,)),
                ),
                "Example_Bank__1.1__1": practices_result("Example_Bank__1.1__1"),
                "Example_Retail__2.2__1": practices_result(
                    "Example_Retail__2.2__1", tag("Named accountability for AI risk")
                ),
            },
        )

    def test_lists_each_tag_by_company_then_code(self, rows: list[PracticeRow]) -> None:
        tags = [(row.mitigation_id, row.practice) for row in rows]

        assert tags == [
            ("Example_Retail__2.2__1", "Named accountability for AI risk"),
            ("Example_Bank__2.2__1", "Named accountability for AI risk"),
            ("Example_Bank__2.2__1", "Published AI policy"),
        ]

    def test_describes_each_tag_with_the_quotes_it_cites(
        self, rows: list[PracticeRow]
    ) -> None:
        assert rows[1:] == [
            PracticeRow(
                mitigation_id="Example_Bank__2.2__1",
                company="Example Bank",
                sector="Finance",
                domain_code="2.2",
                domain_name="Accountability & Responsibility",
                mitigation_name="Board oversight of AI",
                practice="Named accountability for AI risk",
                subtypes="Board of directors oversight",
                reasoning="Fits Named accountability for AI risk.",
                quotes="Our board oversees AI.\n\nIt meets quarterly.",
            ),
            PracticeRow(
                mitigation_id="Example_Bank__2.2__1",
                company="Example Bank",
                sector="Finance",
                domain_code="2.2",
                domain_name="Accountability & Responsibility",
                mitigation_name="Board oversight of AI",
                practice="Published AI policy",
                subtypes="",
                reasoning="Fits Published AI policy.",
                quotes="It meets quarterly.",
            ),
        ]

    def test_rejects_a_cited_quote_the_mitigation_lacks(self) -> None:
        with pytest.raises(ValueError, match="cites quote 3"):
            practice_rows(
                company_names=["Example Bank"],
                taxonomy=TAXONOMY,
                companies=[BANK],
                mitigations=[found_mitigation("Example_Bank__2.2__1", "recA")],
                practices_results={
                    "Example_Bank__2.2__1": practices_result(
                        "Example_Bank__2.2__1",
                        tag("Published AI policy", quote_numbers=(3,)),
                    )
                },
            )


FORUM = "Frontier Model Forum"
PACT = "EU AI Pact"


class TestAffiliationRows:
    @pytest.fixture
    def rows(self) -> list[AffiliationRow]:
        return affiliation_rows(
            company_names=["Example Retail", "Example Bank"],
            taxonomy=TAXONOMY,
            companies=[BANK, RETAIL],
            mitigations=[
                found_mitigation("Example_Bank__2.2__1", "recA"),
                found_mitigation("Example_Bank__1.1__1", "recA"),
                found_mitigation("Example_Retail__2.2__1", "recB"),
            ],
            practices_results={
                "Example_Bank__2.2__1": practices_result(
                    "Example_Bank__2.2__1",
                    affiliations=(
                        Affiliation(
                            name=PACT, relation=Relation.SIGNED, quote_numbers=[1]
                        ),
                        Affiliation(
                            name=FORUM, relation=Relation.MEMBER, quote_numbers=[2]
                        ),
                    ),
                ),
                "Example_Bank__1.1__1": practices_result(
                    "Example_Bank__1.1__1",
                    affiliations=(
                        Affiliation(
                            name=FORUM, relation=Relation.MEMBER, quote_numbers=[1]
                        ),
                    ),
                ),
                "Example_Retail__2.2__1": practices_result(
                    "Example_Retail__2.2__1",
                    affiliations=(
                        Affiliation(
                            name=FORUM,
                            relation=Relation.MEMBER,
                            quote_numbers=[1, 2],
                        ),
                    ),
                ),
            },
        )

    def test_lists_each_name_by_number_of_companies(
        self, rows: list[AffiliationRow]
    ) -> None:
        names = [(row.name, row.company_count, row.mention_count) for row in rows]

        assert names == [(FORUM, 2, 3), (PACT, 1, 1)]

    def test_describes_each_name_with_its_first_mention(
        self, rows: list[AffiliationRow]
    ) -> None:
        assert rows[0] == AffiliationRow(
            name=FORUM,
            relation=Relation.MEMBER,
            company_count=2,
            companies="Example Retail; Example Bank",
            mention_count=3,
            example_mitigation_id="Example_Retail__2.2__1",
            example_quotes="Our board oversees AI.\n\nIt meets quarterly.",
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
