import pytest

from org_mitigations.sync.record_ids import record_ids_by_key
from toolbox.airtable import JsonObject, Record


def _record(record_id: str, fields: JsonObject) -> Record:
    return Record.model_validate(
        {"id": record_id, "createdTime": "2026-11-22T00:00:00.000Z", "fields": fields}
    )


class TestRecordIdsByKey:
    def test_maps_each_key_to_its_record(self) -> None:
        records = [
            _record("recA", {"ID": "Example_Bank__2.2__1", "Note": "Checked"}),
            _record("recB", {"ID": "Example_Bank__2.2__2"}),
        ]

        assert record_ids_by_key(records, "ID") == {
            "Example_Bank__2.2__1": "recA",
            "Example_Bank__2.2__2": "recB",
        }

    def test_rejects_a_record_without_a_key(self) -> None:
        records = [_record("recA", {"Note": "Added by hand"})]

        with pytest.raises(ValueError, match="Record recA has no ID"):
            record_ids_by_key(records, "ID")

    def test_rejects_two_records_with_the_same_key(self) -> None:
        records = [
            _record("recA", {"ID": "Example_Bank__2.2__1"}),
            _record("recB", {"ID": "Example_Bank__2.2__1"}),
        ]

        with pytest.raises(ValueError, match="Records recA and recB have the same ID"):
            record_ids_by_key(records, "ID")
