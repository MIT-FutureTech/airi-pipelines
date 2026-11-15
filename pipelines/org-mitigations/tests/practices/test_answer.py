import pytest
from pydantic import ValidationError

from org_mitigations.practices.answer import (
    Affiliation,
    Answer,
    Relation,
    TaggedPractice,
)


class TestAnswer:
    def test_reads_an_answer_with_practices_and_affiliations(self) -> None:
        answer = Answer.model_validate_json("""{
            "match_id": "Example_Bank__2.2__3",
            "classifications": [
                {
                    "practice": "Formal AI oversight and accountability",
                    "subtypes": ["Board of directors oversight"],
                    "quotes": [1],
                    "reasoning": "A board committee oversees the risks of AI."
                }
            ],
            "named": [
                {"name": "Frontier Model Forum", "relation": "member", "quotes": [2]}
            ]
        }""")

        assert answer == Answer(
            match_id="Example_Bank__2.2__3",
            classifications=[
                TaggedPractice(
                    practice="Formal AI oversight and accountability",
                    subtypes=["Board of directors oversight"],
                    quotes=[1],
                    reasoning="A board committee oversees the risks of AI.",
                )
            ],
            named=[
                Affiliation(
                    name="Frontier Model Forum",
                    relation=Relation.MEMBER,
                    quotes=[2],
                )
            ],
        )

    def test_reads_an_answer_without_practices(self) -> None:
        answer = Answer.model_validate_json(
            '{"match_id": "Example_Bank__1.8__1", "classifications": [], "named": []}'
        )

        assert answer.classifications == []
        assert answer.named == []

    def test_rejects_an_unknown_relation(self) -> None:
        with pytest.raises(ValidationError, match="relation"):
            Affiliation.model_validate(
                {"name": "EU AI Pact", "relation": "supporter", "quotes": [1]}
            )
