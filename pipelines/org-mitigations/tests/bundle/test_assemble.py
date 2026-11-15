import pytest

from org_mitigations.bundle.assemble import Bundle, LocatedEvidence, assemble_bundle
from org_mitigations.bundle.run_settings import RunSettings
from org_mitigations.companies import Company
from org_mitigations.documents import Document
from org_mitigations.domain_taxonomy import Domain, Locus
from org_mitigations.evidence import Evidence
from org_mitigations.excerpts import Excerpt
from org_mitigations.locate import Span
from org_mitigations.search.answer import Strength

RUN = RunSettings(
    prompt_file="prompt.md",
    model="example/model",
    temperature=1.0,
    reasoning_effort="medium",
)
TAXONOMY = [
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
BANK = Company(company_id="recA", name="Example Bank", sector="Finance")
RETAIL = Company(company_id="recB", name="Example Retail", sector="Trade")


def document(document_id: str, company_id: str) -> Document:
    return Document(
        document_id=document_id,
        company_id=company_id,
        title=f"{document_id} title",
        doc_type="Annual report",
        date=None,
        date_precision=None,
        link=f"https://example.com/{document_id}.pdf",
    )


def excerpt(excerpt_id: str, document_id: str, text: str) -> Excerpt:
    return Excerpt(
        excerpt_id=excerpt_id,
        document_id=document_id,
        text=text,
        passage_ids=[f"{document_id}_100"],
    )


def evidence(document_id: str, excerpt_id: str, quote: str) -> Evidence:
    return Evidence(
        evidence_id=f"{document_id}__2.2__1.1",
        mitigation_id=f"{document_id}__2.2__1",
        document_id=document_id,
        domain_code="2.2",
        mitigation="Board oversight of AI",
        reasoning="Board-level accountability for AI.",
        quote=quote,
        strength=Strength.STATED,
        excerpt_id=excerpt_id,
    )


@pytest.fixture
def bundle() -> Bundle:
    return assemble_bundle(
        company_names=["Example Bank"],
        run=RUN,
        taxonomy=TAXONOMY,
        companies=[BANK, RETAIL],
        documents=[
            document("Bank_001", "recA"),
            document("Bank_002", "recA"),
            document("Bank_003", "recA"),
            document("Retail_001", "recB"),
        ],
        excerpts=[
            excerpt("Bank_001_excerpt1", "Bank_001", "Our board\noversees AI."),
            excerpt("Bank_001_excerpt2", "Bank_001", "We use AI for fraud checks."),
            excerpt("Bank_002_excerpt1", "Bank_002", "AI may affect our results."),
            excerpt("Retail_001_excerpt1", "Retail_001", "Our board oversees AI."),
        ],
        evidence=[
            evidence("Bank_001", "Bank_001_excerpt1", "Our board oversees AI."),
            evidence("Bank_001", "Bank_001_excerpt1", "The board oversees AI."),
            evidence("Retail_001", "Retail_001_excerpt1", "Our board oversees AI."),
        ],
    )


class TestAssembleBundle:
    def test_keeps_the_named_companies(self, bundle: Bundle) -> None:
        assert bundle.companies == [BANK]

    def test_keeps_their_documents_with_excerpts(self, bundle: Bundle) -> None:
        document_ids = [document.document_id for document in bundle.documents]

        assert document_ids == ["Bank_001", "Bank_002"]

    def test_keeps_the_excerpts_with_evidence(self, bundle: Bundle) -> None:
        excerpt_ids = [excerpt.excerpt_id for excerpt in bundle.excerpts]

        assert excerpt_ids == ["Bank_001_excerpt1"]

    def test_locates_each_quote(self, bundle: Bundle) -> None:
        assert bundle.evidence == [
            LocatedEvidence(
                **evidence(
                    "Bank_001", "Bank_001_excerpt1", "Our board oversees AI."
                ).model_dump(),
                location=Span(start=0, end=22),
            ),
            LocatedEvidence(
                **evidence(
                    "Bank_001", "Bank_001_excerpt1", "The board oversees AI."
                ).model_dump(),
                location=None,
            ),
        ]

    def test_rejects_an_unknown_company(self) -> None:
        with pytest.raises(KeyError, match="Example Insurer"):
            assemble_bundle(
                company_names=["Example Insurer"],
                run=RUN,
                taxonomy=TAXONOMY,
                companies=[BANK, RETAIL],
                documents=[],
                excerpts=[],
                evidence=[],
            )
