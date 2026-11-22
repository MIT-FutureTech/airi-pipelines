import pytest

from org_mitigations.evidence import Evidence
from org_mitigations.excerpts import merge_passages
from org_mitigations.passages import Passage
from org_mitigations.search.answer import Strength
from org_mitigations.sync.quotes import QuoteRecord, quote_records

SHARED = (
    "The board reviews every AI model before it is deployed"
    + " and records its decision in a register. "
)
PASSAGES = [
    Passage(
        passage_id="Example_Bank_001_0",
        document_id="Example_Bank_001",
        offset=0,
        text="Our bank uses AI across its operations. " + SHARED,
    ),
    Passage(
        passage_id="Example_Bank_001_40",
        document_id="Example_Bank_001",
        offset=40,
        text=SHARED + "Staff complete AI risk training each year.",
    ),
]
PASSAGE_RECORD_IDS = {
    "Example_Bank_001_0": "recPassageA",
    "Example_Bank_001_40": "recPassageB",
}


def _evidence(quote: str) -> Evidence:
    return Evidence(
        evidence_id="Example_Bank__2.2__1.1",
        mitigation_id="Example_Bank__2.2__1",
        document_id="Example_Bank_001",
        domain_code="2.2",
        mitigation_name="AI model review",
        reasoning="The board reviews models.",
        quote=quote,
        strength=Strength.DESCRIBED,
        excerpt_id="Example_Bank_001_excerpt1",
    )


def _passage_record_ids(quote: str) -> list[str]:
    [record] = quote_records(
        evidence=[_evidence(quote)],
        excerpts=merge_passages(PASSAGES),
        passages=PASSAGES,
        mitigation_record_ids={"Example_Bank__2.2__1": "recMitigation"},
        document_record_ids={"Example_Bank_001": "recDocument"},
        passage_record_ids=PASSAGE_RECORD_IDS,
    )
    return record.passage_record_ids


class TestQuoteRecords:
    def test_links_a_quote_to_its_mitigation_and_document(self) -> None:
        quote = "records its decision in a register"
        [record] = quote_records(
            evidence=[_evidence(quote)],
            excerpts=merge_passages(PASSAGES),
            passages=PASSAGES,
            mitigation_record_ids={"Example_Bank__2.2__1": "recMitigation"},
            document_record_ids={"Example_Bank_001": "recDocument"},
            passage_record_ids=PASSAGE_RECORD_IDS,
        )

        assert record == QuoteRecord(
            evidence_id="Example_Bank__2.2__1.1",
            mitigation_record_id="recMitigation",
            document_record_id="recDocument",
            passage_record_ids=["recPassageA", "recPassageB"],
            quote=quote,
            strength=Strength.DESCRIBED,
        )
        assert record.model_dump(mode="json", by_alias=True) == {
            "ID": "Example_Bank__2.2__1.1",
            "Mitigation": ["recMitigation"],
            "Document": ["recDocument"],
            "Passages": ["recPassageA", "recPassageB"],
            "Quote": quote,
            "Strength": "Described",
        }

    @pytest.mark.parametrize(
        ("quote", "expected"),
        [
            ("Our bank uses AI", ["recPassageA"]),
            ("Staff complete AI risk training", ["recPassageB"]),
            ("operations. The board reviews", ["recPassageA", "recPassageB"]),
        ],
    )
    def test_links_only_the_passages_a_quote_overlaps(
        self, quote: str, expected: list[str]
    ) -> None:
        assert _passage_record_ids(quote) == expected

    def test_links_every_passage_when_the_quote_isnt_found(self) -> None:
        assert _passage_record_ids("The bank sells AI to customers") == [
            "recPassageA",
            "recPassageB",
        ]
