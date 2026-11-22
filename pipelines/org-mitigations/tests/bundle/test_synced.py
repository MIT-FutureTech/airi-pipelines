import pytest
from pydantic import ValidationError

from org_mitigations.bundle.synced import (
    SyncedCode,
    SyncedMitigation,
    SyncedQuote,
    read_synced,
)
from org_mitigations.search.answer import Strength
from org_mitigations.sync.codes import Taxonomy
from org_mitigations.sync.mitigations import Status
from toolbox.airtable import JsonObject, Record


def _record(record_id: str, fields: JsonObject) -> Record:
    return Record.model_validate(
        {"id": record_id, "createdTime": "2026-11-22T00:00:00.000Z", "fields": fields}
    )


MITIGATION_FIELDS: JsonObject = {
    "ID": "Example_Bank__2.2__1",
    "Company": ["recBank"],
    "Domain": ["recDomain22"],
    "Instrument": ["recInstrument23"],
    "Name": "AI oversight board",
    "Search reasoning": "A board holds the bank to account.",
    "Instrument reasoning": "An internal policy.",
    "Pipeline run": "2026-11-15T22-05-15+0000",
    "Status": "Current",
    "Note": "Checked by hand",
}


class TestReadSynced:
    def test_reads_a_practice_with_its_empty_fields_left_out(self) -> None:
        record = _record(
            "recModelCards",
            {
                "Key": "Practice Model cards",
                "Taxonomy": "Practice",
                "Name": "Model cards",
                "Order": 1,
                "Definition": "A published card for each model.",
                "Details": "Counts: Model cards.",
            },
        )

        assert read_synced(record, SyncedCode).model_dump() == {
            "record_id": "recModelCards",
            "key": "Practice Model cards",
            "taxonomy": Taxonomy.PRACTICE,
            "code": None,
            "name": "Model cards",
            "short_name": None,
            "group": None,
            "order": 1,
            "definition": "A published card for each model.",
            "details": "Counts: Model cards.",
        }

    def test_reads_a_mitigation_without_practices(self) -> None:
        record = _record("recMitigation", MITIGATION_FIELDS)

        mitigation = read_synced(record, SyncedMitigation)

        assert mitigation.status == Status.CURRENT
        assert mitigation.model_dump() == {
            "record_id": "recMitigation",
            "mitigation_id": "Example_Bank__2.2__1",
            "company_id": "recBank",
            "domain_record_id": "recDomain22",
            "instrument_record_id": "recInstrument23",
            "practice_record_ids": [],
            "name": "AI oversight board",
            "search_reasoning": "A board holds the bank to account.",
            "instrument_reasoning": "An internal policy.",
            "practice_tags": None,
            "pipeline_run": "2026-11-15T22-05-15+0000",
        }

    def test_rejects_two_records_in_a_single_link(self) -> None:
        record = _record(
            "recMitigation", {**MITIGATION_FIELDS, "Company": ["recBank", "recRetail"]}
        )

        with pytest.raises(ValidationError, match="Expected one linked record"):
            read_synced(record, SyncedMitigation)

    def test_reads_a_quote(self) -> None:
        record = _record(
            "recQuote",
            {
                "ID": "Example_Bank__2.2__1.1",
                "Mitigation": ["recMitigation"],
                "Document": ["recDocument"],
                "Passages": ["recPassageA", "recPassageB"],
                "Quote": "The board oversees AI.",
                "Strength": "Described",
            },
        )

        assert read_synced(record, SyncedQuote).model_dump() == {
            "record_id": "recQuote",
            "evidence_id": "Example_Bank__2.2__1.1",
            "mitigation_record_id": "recMitigation",
            "document_record_id": "recDocument",
            "passage_record_ids": ["recPassageA", "recPassageB"],
            "quote": "The board oversees AI.",
            "strength": Strength.DESCRIBED,
        }
