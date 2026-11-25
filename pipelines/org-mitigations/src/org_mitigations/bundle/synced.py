from typing import Annotated

from pydantic import BaseModel, BeforeValidator, Field

from org_mitigations.search.answer import Strength
from org_mitigations.sync.codes import Taxonomy
from org_mitigations.sync.mitigations import Status
from toolbox.airtable import Record


def _only_record_id(record_ids: list[str]) -> str:
    if len(record_ids) != 1:
        raise ValueError(f"Expected one linked record, got {record_ids}")
    return record_ids[0]


type _SingleLink = Annotated[str, BeforeValidator(_only_record_id)]


class SyncedCode(BaseModel):
    record_id: str
    key: str = Field(validation_alias="Key")
    taxonomy: Taxonomy = Field(validation_alias="Taxonomy")
    code: str | None = Field(default=None, validation_alias="Code")
    name: str = Field(validation_alias="Name")
    short_name: str | None = Field(default=None, validation_alias="Short name")
    group: str | None = Field(default=None, validation_alias="Group")
    order: int = Field(validation_alias="Order")
    definition: str = Field(validation_alias="Definition")
    details: str | None = Field(default=None, validation_alias="Details")


class SyncedMitigation(BaseModel):
    record_id: str
    mitigation_id: str = Field(validation_alias="ID")
    company_id: _SingleLink = Field(validation_alias="Company")
    domain_record_id: _SingleLink = Field(validation_alias="Domain")
    instrument_record_id: _SingleLink = Field(validation_alias="Instrument")
    practice_record_ids: list[str] = Field(
        default_factory=list, validation_alias="Practices"
    )
    name: str = Field(validation_alias="Name")
    search_reasoning: str = Field(validation_alias="Search reasoning")
    instrument_reasoning: str = Field(validation_alias="Instrument reasoning")
    practice_tags: str | None = Field(default=None, validation_alias="Practice tags")
    pipeline_run: str = Field(validation_alias="Pipeline run")
    status: Status = Field(validation_alias="Status", exclude=True)


class SyncedQuote(BaseModel):
    record_id: str
    evidence_id: str = Field(validation_alias="ID")
    mitigation_record_id: _SingleLink = Field(validation_alias="Mitigation")
    document_record_id: _SingleLink = Field(validation_alias="Document")
    passage_record_ids: list[str] = Field(validation_alias="Passages")
    quote: str = Field(validation_alias="Quote")
    strength: Annotated[Strength, BeforeValidator(str.lower)] = Field(
        validation_alias="Strength"
    )


def read_synced[Synced: BaseModel](record: Record, synced_type: type[Synced]) -> Synced:
    """Read a record the sync wrote. Airtable leaves out fields that are empty."""
    return synced_type.model_validate({"record_id": record.id, **record.fields})
