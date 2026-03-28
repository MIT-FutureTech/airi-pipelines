from datetime import UTC, datetime

from toolbox.airtable import Record

RECORD_JSON = {
    "id": "rec001",
    "createdTime": "2026-01-15T10:30:00.000Z",
    "fields": {"Name": "Ada", "Status": "Active"},
}


class TestRecord:
    def test_from_api_json(self) -> None:
        record = Record.model_validate(RECORD_JSON)
        assert record.id == "rec001"
        assert record.fields["Name"] == "Ada"
        assert record.created_time == datetime(
            2026,
            1,
            15,
            10,
            30,
            tzinfo=UTC,
        )
