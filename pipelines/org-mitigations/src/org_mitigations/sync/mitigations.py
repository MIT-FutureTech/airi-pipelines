from collections.abc import Mapping
from enum import StrEnum

from pydantic import BaseModel, Field, field_serializer

from org_mitigations.instruments.calls import InstrumentsResult
from org_mitigations.practices.answer import TaggedPractice
from org_mitigations.practices.calls import PracticesResult
from org_mitigations.search.mitigations import FoundMitigation
from org_mitigations.sync.codes import domain_key, instrument_key, practice_key
from org_mitigations.sync.schema import FieldType


class Status(StrEnum):
    CURRENT = "Current"
    EXCLUDED = "Excluded"
    RETIRED = "Retired"


class MitigationRecord(BaseModel):
    mitigation_id: str = Field(serialization_alias="ID")
    company_record_id: str = Field(serialization_alias="Company")
    domain_record_id: str = Field(serialization_alias="Domain")
    instrument_record_id: str = Field(serialization_alias="Instrument")
    practice_record_ids: list[str] = Field(serialization_alias="Practices")
    name: str = Field(serialization_alias="Name")
    search_reasoning: str = Field(serialization_alias="Search reasoning")
    instrument_reasoning: str = Field(serialization_alias="Instrument reasoning")
    practice_tags: str | None = Field(serialization_alias="Practice tags")
    pipeline_run: str = Field(serialization_alias="Pipeline run")
    status: Status = Field(serialization_alias="Status")

    @field_serializer("company_record_id", "domain_record_id", "instrument_record_id")
    def _serialize_link(self, record_id: str) -> list[str]:
        return [record_id]


MITIGATION_FIELD_TYPES = {
    "ID": FieldType.SINGLE_LINE_TEXT,
    "Company": FieldType.LINKS,
    "Domain": FieldType.LINKS,
    "Instrument": FieldType.LINKS,
    "Practices": FieldType.LINKS,
    "Name": FieldType.SINGLE_LINE_TEXT,
    "Search reasoning": FieldType.LONG_TEXT,
    "Instrument reasoning": FieldType.LONG_TEXT,
    "Practice tags": FieldType.LONG_TEXT,
    "Pipeline run": FieldType.SINGLE_LINE_TEXT,
    "Status": FieldType.SINGLE_SELECT,
}


def mitigation_records(
    *,
    mitigations: list[FoundMitigation],
    practices_results: Mapping[str, PracticesResult],
    instruments_results: Mapping[str, InstrumentsResult],
    code_record_ids: Mapping[str, str],
    pipeline_run: str,
) -> list[MitigationRecord]:
    for stage, results in [
        ("practices", practices_results),
        ("instruments", instruments_results),
    ]:
        missing = [
            mitigation.mitigation_id
            for mitigation in mitigations
            if mitigation.mitigation_id not in results
        ]
        if missing:
            raise ValueError(
                f"No {stage} result for {len(missing)} of {len(mitigations)}"
                + f" mitigations, such as {missing[0]}"
            )
    records: list[MitigationRecord] = []
    for mitigation in mitigations:
        tagged = practices_results[mitigation.mitigation_id].answer.tagged_practices
        instrument = instruments_results[mitigation.mitigation_id].answer
        records.append(
            MitigationRecord(
                mitigation_id=mitigation.mitigation_id,
                company_record_id=mitigation.company_id,
                domain_record_id=code_record_ids[domain_key(mitigation.domain_code)],
                instrument_record_id=code_record_ids[
                    instrument_key(instrument.instrument_code)
                ],
                practice_record_ids=[
                    code_record_ids[practice_key(practice.name)] for practice in tagged
                ],
                name=mitigation.name,
                search_reasoning=mitigation.reasoning,
                instrument_reasoning=instrument.reasoning,
                practice_tags=(
                    "\n\n".join(_describe_practice(practice) for practice in tagged)
                    if tagged
                    else None
                ),
                pipeline_run=pipeline_run,
                status=Status.CURRENT,
            )
        )
    return records


def _describe_practice(practice: TaggedPractice) -> str:
    if practice.subtypes:
        return f"{practice.name} ({'; '.join(practice.subtypes)}): {practice.reasoning}"
    return f"{practice.name}: {practice.reasoning}"
