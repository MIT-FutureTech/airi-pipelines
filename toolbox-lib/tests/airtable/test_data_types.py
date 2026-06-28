from datetime import UTC, datetime

import pytest

from toolbox.airtable import Record

RECORD_JSON = {
    "id": "rec001",
    "createdTime": "2026-01-15T10:30:00.000Z",
    "fields": {"Name": "Ada", "Status": "Active"},
}

ATTACHMENT_JSON = {
    "id": "att001",
    "url": "https://example.com/file.pdf",
    "filename": "file.pdf",
    "size": 1234,
    "type": "application/pdf",
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


class TestRecordAttachments:
    def test_parses_attachment_objects(self) -> None:
        record = Record.model_validate(
            {**RECORD_JSON, "fields": {"Files": [ATTACHMENT_JSON]}}
        )
        attachments = record.attachments("Files")

        assert len(attachments) == 1
        assert attachments[0].id == "att001"
        assert attachments[0].url == "https://example.com/file.pdf"
        assert attachments[0].filename == "file.pdf"

    def test_absent_field_raises_error(self) -> None:
        record = Record.model_validate(RECORD_JSON)
        with pytest.raises(KeyError):
            record.attachments("Files")

    def test_empty_field_returns_empty(self) -> None:
        record = Record.model_validate({**RECORD_JSON, "fields": {"Files": []}})
        assert record.attachments("Files") == []

    def test_non_attachment_field_raises(self) -> None:
        record = Record.model_validate(RECORD_JSON)
        with pytest.raises(TypeError, match="not an attachment field"):
            record.attachments("Name")
