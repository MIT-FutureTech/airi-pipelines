import json
from pathlib import Path

from org_mitigations.evidence import Evidence, evidence_from_mitigations, load_evidence
from org_mitigations.excerpts import Excerpt
from org_mitigations.search.answer import Strength
from org_mitigations.search.mitigations import FoundMitigation, FoundQuote

WITH_MITIGATIONS: dict[str, object] = {
    "input": {
        "match_id": "Example_Bank_002_part2__2.2",
        "company": "Example Bank",
        "document_id": "Example_Bank_002",
        "code": "2.2",
        "context": '<excerpt id="1">[...] Our board oversees AI. [...]</excerpt>',
    },
    "result": {
        "match_id": "Example_Bank_002_part2__2.2",
        "has_mitigation": True,
        "reason": "The board oversees AI.",
        "classifications": [
            {
                "mitigation": "Board oversight of AI",
                "evidence": [
                    {
                        "excerpt": "1",
                        "quote": "Our board oversees AI.",
                        "strength": "stated",
                    },
                    {
                        "excerpt": "3",
                        "quote": "The board's risk committee reviews AI risks.",
                        "strength": "described",
                    },
                ],
                "reasoning": "Board-level accountability for AI.",
            },
            {
                "mitigation": "AI governance policy",
                "evidence": [
                    {
                        "excerpt": "2",
                        "quote": "our AI Governance Policy",
                        "strength": "reference",
                    },
                ],
                "reasoning": "A policy setting roles for AI.",
            },
        ],
    },
    "metadata": {"llm_model": "google/gemini-3.5-flash", "llm_error": ""},
}

WITHOUT_MITIGATIONS: dict[str, object] = {
    "input": {
        "match_id": "Example_Bank_001__1.1",
        "company": "Example Bank",
        "document_id": "Example_Bank_001",
        "code": "1.1",
        "context": '<excerpt id="1">[...] We value transparency. [...]</excerpt>',
    },
    "result": {
        "match_id": "Example_Bank_001__1.1",
        "has_mitigation": False,
        "reason": "Aspirational statements only.",
        "classifications": [],
    },
    "metadata": {"llm_model": "google/gemini-3.5-flash", "llm_error": ""},
}


class TestLoadEvidence:
    def test_reads_one_record_per_quote(self, tmp_path: Path) -> None:
        (tmp_path / "Example_Bank_002_part2__2.2.json").write_text(
            json.dumps(WITH_MITIGATIONS)
        )
        (tmp_path / "Example_Bank_001__1.1.json").write_text(
            json.dumps(WITHOUT_MITIGATIONS)
        )
        (tmp_path / "log.txt").write_text("Classified 2 rows")

        assert load_evidence(tmp_path) == [
            Evidence(
                evidence_id="Example_Bank_002_part2__2.2__1.1",
                mitigation_id="Example_Bank_002_part2__2.2__1",
                document_id="Example_Bank_002",
                domain_code="2.2",
                mitigation_name="Board oversight of AI",
                reasoning="Board-level accountability for AI.",
                quote="Our board oversees AI.",
                strength=Strength.STATED,
                excerpt_id="Example_Bank_002_part2_excerpt1",
            ),
            Evidence(
                evidence_id="Example_Bank_002_part2__2.2__1.2",
                mitigation_id="Example_Bank_002_part2__2.2__1",
                document_id="Example_Bank_002",
                domain_code="2.2",
                mitigation_name="Board oversight of AI",
                reasoning="Board-level accountability for AI.",
                quote="The board's risk committee reviews AI risks.",
                strength=Strength.DESCRIBED,
                excerpt_id="Example_Bank_002_part2_excerpt3",
            ),
            Evidence(
                evidence_id="Example_Bank_002_part2__2.2__2.1",
                mitigation_id="Example_Bank_002_part2__2.2__2",
                document_id="Example_Bank_002",
                domain_code="2.2",
                mitigation_name="AI governance policy",
                reasoning="A policy setting roles for AI.",
                quote="our AI Governance Policy",
                strength=Strength.REFERENCE,
                excerpt_id="Example_Bank_002_part2_excerpt2",
            ),
        ]


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
