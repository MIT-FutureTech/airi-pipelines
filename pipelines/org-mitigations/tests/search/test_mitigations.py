import pytest

from org_mitigations.search.answer import Answer, Mitigation, Quote, Strength
from org_mitigations.search.calls import SearchResult
from org_mitigations.search.context import Context
from org_mitigations.search.mitigations import (
    FoundMitigation,
    FoundQuote,
    mitigations_from_results,
)

CONTEXTS = [
    Context(
        context_id="Example_Bank",
        company_id="recA",
        text="<document>bank</document>",
        excerpt_ids=["Example_Bank_001_excerpt1", "Example_Bank_002_excerpt1"],
    ),
]


def _result(code: str, mitigations: list[Mitigation]) -> SearchResult:
    return SearchResult(
        context_id="Example_Bank",
        code=code,
        answer=Answer(
            match_id=f"Example_Bank__{code}",
            has_mitigation=bool(mitigations),
            reason=None,
            classifications=mitigations,
        ),
        model="google/gemini-3.5-flash",
        usage=None,
    )


def _mitigation(name: str, *excerpts: int) -> Mitigation:
    return Mitigation(
        mitigation=name,
        evidence=[
            Quote(
                excerpt=excerpt, quote=f"Quote from {excerpt}", strength=Strength.STATED
            )
            for excerpt in excerpts
        ],
        reasoning=f"Why {name}",
    )


class TestFoundMitigations:
    def test_lists_each_mitigation_with_its_quotes_excerpts(self) -> None:
        results = {
            "Example_Bank__1.1": _result("1.1", []),
            "Example_Bank__2.2": _result(
                "2.2",
                [_mitigation("Board oversight", 2), _mitigation("AI policy", 1, 2)],
            ),
        }

        assert mitigations_from_results(results, CONTEXTS) == [
            FoundMitigation(
                mitigation_id="Example_Bank__2.2__1",
                company_id="recA",
                code="2.2",
                name="Board oversight",
                reasoning="Why Board oversight",
                quotes=[
                    FoundQuote(
                        excerpt_id="Example_Bank_002_excerpt1",
                        quote="Quote from 2",
                        strength=Strength.STATED,
                    ),
                ],
            ),
            FoundMitigation(
                mitigation_id="Example_Bank__2.2__2",
                company_id="recA",
                code="2.2",
                name="AI policy",
                reasoning="Why AI policy",
                quotes=[
                    FoundQuote(
                        excerpt_id="Example_Bank_001_excerpt1",
                        quote="Quote from 1",
                        strength=Strength.STATED,
                    ),
                    FoundQuote(
                        excerpt_id="Example_Bank_002_excerpt1",
                        quote="Quote from 2",
                        strength=Strength.STATED,
                    ),
                ],
            ),
        ]

    @pytest.mark.parametrize("excerpt", [0, 3])
    def test_rejects_an_excerpt_the_context_lacks(self, excerpt: int) -> None:
        results = {
            "Example_Bank__2.2": _result("2.2", [_mitigation("AI policy", excerpt)])
        }

        with pytest.raises(ValueError, match=f"cites excerpt {excerpt}"):
            mitigations_from_results(results, CONTEXTS)
