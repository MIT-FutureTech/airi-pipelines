import pytest
from pydantic import ValidationError

from org_mitigations.practice_list import Practice
from org_mitigations.practices.answer import (
    Affiliation,
    Answer,
    Relation,
    TaggedPractice,
    unlisted_names,
)

PRACTICES = [
    Practice(
        name="Red teaming",
        definition="Red teaming is a testing method.",
        counts=["Internal and external red teams."],
        does_not_count=["Ordinary quality testing."],
        subtypes=["External red teaming", "Automated red teaming"],
    ),
    Practice(
        name="Published AI policy",
        definition="A published AI policy is an organisational policy.",
        counts=["A named, published document of responsible AI principles."],
        does_not_count=["Passing statements of values."],
        subtypes=[],
    ),
]


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


def _tagged(practice: str, *subtypes: str) -> TaggedPractice:
    return TaggedPractice(
        practice=practice, subtypes=list(subtypes), quotes=[1], reasoning="Fits."
    )


def _answer(*tagged: TaggedPractice) -> Answer:
    return Answer(
        match_id="Example_Bank__1.4__1", classifications=list(tagged), named=[]
    )


class TestUnlistedNames:
    def test_finds_none_when_every_name_is_listed(self) -> None:
        answer = _answer(
            _tagged("Red teaming", "External red teaming"),
            _tagged("Published AI policy"),
        )

        assert unlisted_names(answer, PRACTICES) == []

    def test_finds_a_practice_missing_from_the_list(self) -> None:
        answer = _answer(_tagged("Red-teaming", "External red teaming"))

        assert unlisted_names(answer, PRACTICES) == ["practice 'Red-teaming'"]

    def test_finds_a_subtype_the_practice_lacks(self) -> None:
        answer = _answer(
            _tagged("Red teaming", "Automated red teaming", "Bias testing"),
            _tagged("Published AI policy", "External red teaming"),
        )

        assert unlisted_names(answer, PRACTICES) == [
            "subtype 'Bias testing' of 'Red teaming'",
            "subtype 'External red teaming' of 'Published AI policy'",
        ]
