from org_mitigations.instrument_taxonomy import Instrument, Modality
from org_mitigations.instruments.answer import Answer, invalid_code_reason


def _instrument(code: str, name: str) -> Instrument:
    return Instrument(
        code=code,
        name=name,
        short_name=name,
        definition=f"Mitigations that work through {name}.",
        scope=None,
        examples=[],
        exclusions=None,
    )


MODALITIES = [
    Modality(
        code="2",
        name="Govern",
        instruments=[
            _instrument("2.2", "External Standards"),
            _instrument("2.3", "Internal Policies"),
        ],
    ),
    Modality(
        code="3",
        name="Implement",
        instruments=[_instrument("3.2", "Practices & Processes")],
    ),
]


def _answer(modality: str, instrument_code: str) -> Answer:
    return Answer(
        lever="Creating a rule for itself.",
        modality=modality,
        instrument_code=instrument_code,
        reasoning="Self-authored internal rule.",
    )


class TestAnswer:
    def test_reads_an_answer(self) -> None:
        answer = Answer.model_validate_json("""{
            "lever": "Creating a rule for itself, internally.",
            "modality": "2",
            "instrument_code": "2.3",
            "reasoning": "Self-authored internal rule — Internal Policies."
        }""")

        assert answer == Answer(
            lever="Creating a rule for itself, internally.",
            modality="2",
            instrument_code="2.3",
            reasoning="Self-authored internal rule — Internal Policies.",
        )


class TestInvalidCodeReason:
    def test_finds_none_when_the_modality_contains_the_code(self) -> None:
        assert invalid_code_reason(_answer("2", "2.3"), MODALITIES) is None

    def test_finds_a_code_missing_from_the_taxonomy(self) -> None:
        assert (
            invalid_code_reason(_answer("2", "2.4"), MODALITIES)
            == "Instrument code '2.4' isn't in the taxonomy"
        )

    def test_finds_a_modality_that_lacks_the_code(self) -> None:
        assert (
            invalid_code_reason(_answer("3", "2.3"), MODALITIES)
            == "Modality '3' doesn't contain instrument code '2.3'"
        )
