import pytest
from pydantic import ValidationError

from org_mitigations.search.answer import Answer, Mitigation, Quote, Strength


class TestAnswer:
    def test_reads_an_answer_with_mitigations(self) -> None:
        answer = Answer.model_validate_json("""{
            "match_id": "Example_Bank__2.1",
            "has_mitigation": true,
            "reason": null,
            "mitigations": [
                {
                    "name": "Responsible AI training for staff",
                    "quotes": [
                        {
                            "excerpt_number": 1,
                            "quote": "We require all employees to complete training",
                            "strength": "described"
                        }
                    ],
                    "reasoning": "Builds the AI-safety knowledge of staff."
                }
            ]
        }""")

        assert answer == Answer(
            match_id="Example_Bank__2.1",
            has_mitigation=True,
            reason=None,
            mitigations=[
                Mitigation(
                    name="Responsible AI training for staff",
                    quotes=[
                        Quote(
                            excerpt_number=1,
                            quote="We require all employees to complete training",
                            strength=Strength.DESCRIBED,
                        )
                    ],
                    reasoning="Builds the AI-safety knowledge of staff.",
                )
            ],
        )

    def test_reads_an_answer_without_mitigations(self) -> None:
        answer = Answer.model_validate_json("""{
            "match_id": "Example_Bank__1.3",
            "has_mitigation": false,
            "reason": "Policy and training; nothing bounds model capabilities",
            "mitigations": []
        }""")

        assert answer.reason == "Policy and training; nothing bounds model capabilities"
        assert answer.mitigations == []

    def test_rejects_an_unknown_strength(self) -> None:
        with pytest.raises(ValidationError, match="strength"):
            Quote.model_validate(
                {"excerpt_number": 1, "quote": "We test models", "strength": "strong"}
            )
