import pytest

from org_mitigations.bundle.build import BundleQuote, build_bundle
from org_mitigations.bundle.synced import (
    SyncedCode,
    SyncedMitigation,
    SyncedQuote,
    read_synced,
)
from org_mitigations.companies import Company
from org_mitigations.documents import Document
from org_mitigations.excerpts import merge_passages
from org_mitigations.locate import Span
from org_mitigations.passages import Passage
from org_mitigations.search.answer import Strength
from toolbox.airtable import JsonObject, Record

BANK = Company(company_id="recBank", name="Example Bank", sector="Finance")
INSURER = Company(company_id="recInsurer", name="Example Insurer", sector="Finance")
RETAIL = Company(company_id="recRetail", name="Example Retail", sector="Trade")
BANK_TEXT = "The board reviews every AI model before it is deployed."
INSURER_TEXT = "Staff complete AI risk training each year."
PASSAGES = [
    Passage(
        passage_id="Example_Bank_001_0",
        document_id="Example_Bank_001",
        offset=0,
        text=BANK_TEXT,
    ),
    Passage(
        passage_id="Example_Insurer_001_0",
        document_id="Example_Insurer_001",
        offset=0,
        text=INSURER_TEXT,
    ),
]
PASSAGE_IDS_BY_RECORD_ID = {
    "recBankPassage": "Example_Bank_001_0",
    "recInsurerPassage": "Example_Insurer_001_0",
}
DOCUMENT_IDS_BY_RECORD_ID = {
    "recBankDocument": "Example_Bank_001",
    "recInsurerDocument": "Example_Insurer_001",
}


def _record(record_id: str, fields: JsonObject) -> Record:
    return Record.model_validate(
        {"id": record_id, "createdTime": "2026-11-22T00:00:00.000Z", "fields": fields}
    )


def _code(record_id: str, taxonomy: str, order: int) -> SyncedCode:
    return read_synced(
        _record(
            record_id,
            {
                "Key": f"{taxonomy} {order}",
                "Taxonomy": taxonomy,
                "Name": f"{taxonomy} number {order}",
                "Order": order,
                "Definition": "...",
            },
        ),
        SyncedCode,
    )


def _mitigation(
    record_id: str, mitigation_id: str, company_id: str, status: str
) -> SyncedMitigation:
    return read_synced(
        _record(
            record_id,
            {
                "ID": mitigation_id,
                "Company": [company_id],
                "Domain": ["recDomain"],
                "Instrument": ["recInstrument"],
                "Name": "A mitigation",
                "Search reasoning": "...",
                "Instrument reasoning": "...",
                "Pipeline run": "2026-11-15T22-05-15+0000",
                "Status": status,
            },
        ),
        SyncedMitigation,
    )


def _quote(
    evidence_id: str,
    mitigation_record_id: str,
    document_record_id: str,
    passage_record_ids: list[str],
    quote: str,
) -> SyncedQuote:
    return read_synced(
        _record(
            f"rec{evidence_id}",
            {
                "ID": evidence_id,
                "Mitigation": [mitigation_record_id],
                "Document": [document_record_id],
                "Passages": list(passage_record_ids),
                "Quote": quote,
                "Strength": "Stated",
            },
        ),
        SyncedQuote,
    )


def _document(document_id: str, company_id: str) -> Document:
    return Document(
        document_id=document_id,
        company_id=company_id,
        title=f"{document_id} report",
        doc_type="Annual report",
        date=None,
        date_precision=None,
        link=f"https://example.com/{document_id}.pdf",
    )


DOCUMENTS = [
    _document("Example_Bank_001", "recBank"),
    _document("Example_Bank_002", "recBank"),
    _document("Example_Insurer_001", "recInsurer"),
]


class TestBuildBundle:
    def test_keeps_what_current_mitigations_need(self) -> None:
        bundle = build_bundle(
            codes=[
                _code("recPractice1", "Practice", 1),
                _code("recDomain2", "Domain", 2),
                _code("recDomain1", "Domain", 1),
            ],
            mitigations=[
                _mitigation(
                    "recInsurerM", "Example_Insurer__2.1__1", "recInsurer", "Current"
                ),
                _mitigation("recBankM", "Example_Bank__2.2__1", "recBank", "Current"),
                _mitigation(
                    "recRetailM", "Example_Retail__2.2__1", "recRetail", "Excluded"
                ),
            ],
            quotes=[
                _quote(
                    "Example_Insurer__2.1__1.1",
                    "recInsurerM",
                    "recInsurerDocument",
                    ["recInsurerPassage"],
                    "Not in the passage",
                ),
                _quote(
                    "Example_Bank__2.2__1.1",
                    "recBankM",
                    "recBankDocument",
                    ["recBankPassage"],
                    "reviews every AI model",
                ),
            ],
            companies=[RETAIL, INSURER, BANK],
            documents=DOCUMENTS,
            excerpts=merge_passages(PASSAGES),
            document_ids_by_record_id=DOCUMENT_IDS_BY_RECORD_ID,
            passage_ids_by_record_id=PASSAGE_IDS_BY_RECORD_ID,
        )

        assert [code.record_id for code in bundle.codes] == [
            "recDomain1",
            "recDomain2",
            "recPractice1",
        ]
        assert bundle.companies == [BANK, INSURER]
        assert [document.document_id for document in bundle.documents] == [
            "Example_Bank_001",
            "Example_Insurer_001",
        ]
        assert [excerpt.excerpt_id for excerpt in bundle.excerpts] == [
            "Example_Bank_001_excerpt1",
            "Example_Insurer_001_excerpt1",
        ]
        assert [mitigation.record_id for mitigation in bundle.mitigations] == [
            "recBankM",
            "recInsurerM",
        ]
        start = BANK_TEXT.index("reviews")
        assert bundle.quotes == [
            BundleQuote(
                evidence_id="Example_Bank__2.2__1.1",
                mitigation_record_id="recBankM",
                document_id="Example_Bank_001",
                excerpt_id="Example_Bank_001_excerpt1",
                quote="reviews every AI model",
                strength=Strength.STATED,
                location=Span(start=start, end=start + len("reviews every AI model")),
            ),
            BundleQuote(
                evidence_id="Example_Insurer__2.1__1.1",
                mitigation_record_id="recInsurerM",
                document_id="Example_Insurer_001",
                excerpt_id="Example_Insurer_001_excerpt1",
                quote="Not in the passage",
                strength=Strength.STATED,
                location=None,
            ),
        ]

    def test_rejects_a_quote_whose_passages_are_in_two_excerpts(self) -> None:
        with pytest.raises(ValueError, match="passages are in 2 excerpts, not one"):
            build_bundle(
                codes=[],
                mitigations=[
                    _mitigation(
                        "recBankM", "Example_Bank__2.2__1", "recBank", "Current"
                    )
                ],
                quotes=[
                    _quote(
                        "Example_Bank__2.2__1.1",
                        "recBankM",
                        "recBankDocument",
                        ["recBankPassage", "recInsurerPassage"],
                        "reviews every AI model",
                    )
                ],
                companies=[BANK],
                documents=DOCUMENTS,
                excerpts=merge_passages(PASSAGES),
                document_ids_by_record_id=DOCUMENT_IDS_BY_RECORD_ID,
                passage_ids_by_record_id=PASSAGE_IDS_BY_RECORD_ID,
            )

    def test_rejects_a_mitigation_from_a_company_the_export_lacks(self) -> None:
        with pytest.raises(ValueError, match="companies the export doesn't have"):
            build_bundle(
                codes=[],
                mitigations=[
                    _mitigation(
                        "recBankM", "Example_Bank__2.2__1", "recBank", "Current"
                    )
                ],
                quotes=[],
                companies=[RETAIL],
                documents=DOCUMENTS,
                excerpts=merge_passages(PASSAGES),
                document_ids_by_record_id=DOCUMENT_IDS_BY_RECORD_ID,
                passage_ids_by_record_id=PASSAGE_IDS_BY_RECORD_ID,
            )
