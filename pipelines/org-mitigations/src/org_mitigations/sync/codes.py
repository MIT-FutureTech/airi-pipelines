from enum import StrEnum

from pydantic import BaseModel, Field

from org_mitigations.domain_taxonomy import Domain, Locus
from org_mitigations.instrument_taxonomy import Instrument, Modality
from org_mitigations.practice_list import Practice
from org_mitigations.sync.schema import FieldType


class Taxonomy(StrEnum):
    DOMAIN = "Domain"
    INSTRUMENT = "Instrument"
    PRACTICE = "Practice"


class CodeRecord(BaseModel):
    key: str = Field(serialization_alias="Key")
    taxonomy: Taxonomy = Field(serialization_alias="Taxonomy")
    code: str | None = Field(serialization_alias="Code")
    name: str = Field(serialization_alias="Name")
    short_name: str | None = Field(serialization_alias="Short name")
    group: str | None = Field(serialization_alias="Group")
    order: int = Field(serialization_alias="Order")
    definition: str = Field(serialization_alias="Definition")
    details: str | None = Field(serialization_alias="Details")


CODE_FIELD_TYPES = {
    "Key": FieldType.SINGLE_LINE_TEXT,
    "Taxonomy": FieldType.SINGLE_SELECT,
    "Code": FieldType.SINGLE_LINE_TEXT,
    "Name": FieldType.SINGLE_LINE_TEXT,
    "Short name": FieldType.SINGLE_LINE_TEXT,
    "Group": FieldType.SINGLE_LINE_TEXT,
    "Order": FieldType.NUMBER,
    "Definition": FieldType.LONG_TEXT,
    "Details": FieldType.LONG_TEXT,
}


def domain_key(domain_code: str) -> str:
    return f"{Taxonomy.DOMAIN} {domain_code}"


def instrument_key(instrument_code: str) -> str:
    return f"{Taxonomy.INSTRUMENT} {instrument_code}"


def practice_key(practice_name: str) -> str:
    return f"{Taxonomy.PRACTICE} {practice_name}"


def code_records(
    *,
    domain_taxonomy: list[Locus],
    instrument_taxonomy: list[Modality],
    practices: list[Practice],
) -> list[CodeRecord]:
    domains = [(locus, domain) for locus in domain_taxonomy for domain in locus.domains]
    instruments = [
        (modality, instrument)
        for modality in instrument_taxonomy
        for instrument in modality.instruments
    ]
    return [
        *(
            _domain_record(locus, domain, order)
            for order, (locus, domain) in enumerate(domains, start=1)
        ),
        *(
            _instrument_record(modality, instrument, order)
            for order, (modality, instrument) in enumerate(instruments, start=1)
        ),
        *(
            _practice_record(practice, order)
            for order, practice in enumerate(practices, start=1)
        ),
    ]


def _domain_record(locus: Locus, domain: Domain, order: int) -> CodeRecord:
    details = [
        f"Boundary question: {domain.boundary_question}",
        f"Examples: {'; '.join(domain.examples)}",
    ]
    if domain.exclusions is not None:
        details.append(f"Exclusions: {domain.exclusions}")
    return CodeRecord(
        key=domain_key(domain.code),
        taxonomy=Taxonomy.DOMAIN,
        code=domain.code,
        name=domain.name,
        short_name=domain.short_name,
        group=locus.name,
        order=order,
        definition=domain.definition,
        details="\n".join(details),
    )


def _instrument_record(
    modality: Modality, instrument: Instrument, order: int
) -> CodeRecord:
    details: list[str] = []
    if instrument.scope is not None:
        details.append(f"Scope: {instrument.scope}")
    if instrument.examples:
        details.append(f"Examples: {'; '.join(instrument.examples)}")
    if instrument.exclusions is not None:
        details.append(f"Exclusions: {instrument.exclusions}")
    return CodeRecord(
        key=instrument_key(instrument.code),
        taxonomy=Taxonomy.INSTRUMENT,
        code=instrument.code,
        name=instrument.name,
        short_name=instrument.short_name,
        group=modality.name,
        order=order,
        definition=instrument.definition,
        details="\n".join(details) if details else None,
    )


def _practice_record(practice: Practice, order: int) -> CodeRecord:
    details = [
        f"Counts: {' '.join(practice.counts)}",
        f"Does not count: {' '.join(practice.does_not_count)}",
    ]
    if practice.subtypes:
        details.append(f"Subtypes: {'; '.join(practice.subtypes)}")
    return CodeRecord(
        key=practice_key(practice.name),
        taxonomy=Taxonomy.PRACTICE,
        code=None,
        name=practice.name,
        short_name=None,
        group=None,
        order=order,
        definition=practice.definition,
        details="\n".join(details),
    )
