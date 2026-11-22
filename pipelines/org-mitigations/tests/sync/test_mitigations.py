import pytest

from org_mitigations.instruments.answer import Answer as InstrumentsAnswer
from org_mitigations.instruments.calls import InstrumentsResult
from org_mitigations.practices.answer import Answer as PracticesAnswer
from org_mitigations.practices.answer import TaggedPractice
from org_mitigations.practices.calls import PracticesResult
from org_mitigations.search.answer import Strength
from org_mitigations.search.mitigations import FoundMitigation, FoundQuote
from org_mitigations.sync.mitigations import (
    MitigationRecord,
    Status,
    mitigation_records,
)

CODE_RECORD_IDS = {
    "Domain 2.2": "recDomain22",
    "Instrument 2.3": "recInstrument23",
    "Practice Model cards": "recModelCards",
    "Practice Red teaming": "recRedTeaming",
}


def _mitigation(mitigation_id: str) -> FoundMitigation:
    return FoundMitigation(
        mitigation_id=mitigation_id,
        context_id="Example_Bank",
        company_id="recBank",
        domain_code="2.2",
        name="AI oversight board",
        reasoning="A board that holds the bank to account for AI.",
        quotes=[
            FoundQuote(
                excerpt_id="Example_Bank_001_excerpt1",
                quote="The board oversees AI.",
                strength=Strength.STATED,
            )
        ],
    )


def _practices_result(mitigation_id: str, *tagged: TaggedPractice) -> PracticesResult:
    return PracticesResult(
        mitigation_id=mitigation_id,
        answer=PracticesAnswer(
            match_id=mitigation_id, tagged_practices=list(tagged), affiliations=[]
        ),
        model="test-model",
        usage=None,
    )


def _instruments_result(mitigation_id: str) -> InstrumentsResult:
    return InstrumentsResult(
        mitigation_id=mitigation_id,
        answer=InstrumentsAnswer(
            lever="A rule it sets for itself.",
            modality="2",
            instrument_code="2.3",
            reasoning="An internal policy.",
        ),
        model="test-model",
        usage=None,
    )


class TestMitigationRecords:
    def test_links_a_mitigation_to_its_company_and_codes(self) -> None:
        mitigation_id = "Example_Bank__2.2__1"
        records = mitigation_records(
            mitigations=[_mitigation(mitigation_id)],
            practices_results={
                mitigation_id: _practices_result(
                    mitigation_id,
                    TaggedPractice(
                        name="Model cards",
                        subtypes=[],
                        quote_numbers=[1],
                        reasoning="It publishes cards.",
                    ),
                    TaggedPractice(
                        name="Red teaming",
                        subtypes=["Internal", "External"],
                        quote_numbers=[1],
                        reasoning="It attacks its models.",
                    ),
                )
            },
            instruments_results={mitigation_id: _instruments_result(mitigation_id)},
            code_record_ids=CODE_RECORD_IDS,
            pipeline_run="2026-11-15T22-05-15+0000",
        )

        assert records == [
            MitigationRecord(
                mitigation_id=mitigation_id,
                company_record_id="recBank",
                domain_record_id="recDomain22",
                instrument_record_id="recInstrument23",
                practice_record_ids=["recModelCards", "recRedTeaming"],
                name="AI oversight board",
                search_reasoning="A board that holds the bank to account for AI.",
                instrument_reasoning="An internal policy.",
                practice_tags="Model cards: It publishes cards.\n\n"
                + "Red teaming (Internal; External): It attacks its models.",
                pipeline_run="2026-11-15T22-05-15+0000",
                status=Status.CURRENT,
            )
        ]

    def test_writes_links_as_lists_of_record_ids(self) -> None:
        mitigation_id = "Example_Bank__2.2__1"
        [record] = mitigation_records(
            mitigations=[_mitigation(mitigation_id)],
            practices_results={mitigation_id: _practices_result(mitigation_id)},
            instruments_results={mitigation_id: _instruments_result(mitigation_id)},
            code_record_ids=CODE_RECORD_IDS,
            pipeline_run="2026-11-15T22-05-15+0000",
        )

        fields = record.model_dump(mode="json", by_alias=True)

        assert fields["Company"] == ["recBank"]
        assert fields["Domain"] == ["recDomain22"]
        assert fields["Instrument"] == ["recInstrument23"]
        assert fields["Practices"] == []
        assert fields["Practice tags"] is None

    @pytest.mark.parametrize("stage", ["practices", "instruments"])
    def test_rejects_a_mitigation_without_a_result(self, stage: str) -> None:
        mitigation_id = "Example_Bank__2.2__1"

        with pytest.raises(ValueError, match=f"No {stage} result for 1 of 1"):
            mitigation_records(
                mitigations=[_mitigation(mitigation_id)],
                practices_results=(
                    {}
                    if stage == "practices"
                    else {mitigation_id: _practices_result(mitigation_id)}
                ),
                instruments_results=(
                    {}
                    if stage == "instruments"
                    else {mitigation_id: _instruments_result(mitigation_id)}
                ),
                code_record_ids=CODE_RECORD_IDS,
                pipeline_run="2026-11-15T22-05-15+0000",
            )
