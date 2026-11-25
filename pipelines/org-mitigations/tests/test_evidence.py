from org_mitigations.evidence import Evidence, evidence_from_mitigations
from org_mitigations.excerpts import Excerpt
from org_mitigations.search.answer import Strength
from org_mitigations.search.mitigations import FoundMitigation, FoundQuote


class TestEvidenceFromMitigations:
    def test_lists_each_quote_with_its_document(self) -> None:
        excerpts = [
            Excerpt(
                excerpt_id=f"Example_Bank_00{number}_excerpt1",
                document_id=f"Example_Bank_00{number}",
                text=f"Text of document {number}",
                passage_ids=[f"Example_Bank_00{number}_passage1"],
            )
            for number in [1, 2]
        ]
        mitigations = [
            FoundMitigation(
                mitigation_id="Example_Bank__2.2__1",
                company_id="recA",
                domain_code="2.2",
                name="Board oversight of AI",
                reasoning="Board-level accountability for AI.",
                quotes=[
                    FoundQuote(
                        excerpt_id="Example_Bank_002_excerpt1",
                        quote="Our board oversees AI.",
                        strength=Strength.STATED,
                    ),
                    FoundQuote(
                        excerpt_id="Example_Bank_001_excerpt1",
                        quote="our AI Governance Policy",
                        strength=Strength.REFERENCE,
                    ),
                ],
            ),
        ]

        assert evidence_from_mitigations(mitigations, excerpts) == [
            Evidence(
                evidence_id="Example_Bank__2.2__1.1",
                mitigation_id="Example_Bank__2.2__1",
                document_id="Example_Bank_002",
                domain_code="2.2",
                mitigation_name="Board oversight of AI",
                reasoning="Board-level accountability for AI.",
                quote="Our board oversees AI.",
                strength=Strength.STATED,
                excerpt_id="Example_Bank_002_excerpt1",
            ),
            Evidence(
                evidence_id="Example_Bank__2.2__1.2",
                mitigation_id="Example_Bank__2.2__1",
                document_id="Example_Bank_001",
                domain_code="2.2",
                mitigation_name="Board oversight of AI",
                reasoning="Board-level accountability for AI.",
                quote="our AI Governance Policy",
                strength=Strength.REFERENCE,
                excerpt_id="Example_Bank_001_excerpt1",
            ),
        ]
