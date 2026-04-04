from datetime import datetime
from unittest.mock import AsyncMock

import pytest
from httpx import Response

from toolbox.airtable import FieldSpec, Table, UpdateRecord
from toolbox.airtable.data_types import JsonValue

from .helpers import make_mock_client, make_response

BASE_ID = "appTEST123"
TABLE_NAME = "TestTable"
RECORD_JSON = {
    "id": "rec001",
    "createdTime": "2026-01-15T10:30:00.000Z",
    "fields": {"Name": "Ada", "Status": "Active"},
}
TABLES_JSON = {
    "tables": [
        {
            "id": "tbl001",
            "name": TABLE_NAME,
            "fields": [
                {
                    "id": "fld001",
                    "name": "Name",
                    "type": "singleLineText",
                },
            ],
        },
    ],
}


@pytest.fixture
def success_response() -> Response:
    return make_response(status_code=200, json=RECORD_JSON)


class TestCreate:
    async def test_sends_fields(
        self,
        success_response: Response,
    ) -> None:
        async with make_mock_client([success_response]) as client:
            table = Table(client, BASE_ID, TABLE_NAME)
            record = await table.create({"Name": "Ada"})

            assert record.id == "rec001"
            assert isinstance(client._http_client.request, AsyncMock)
            body = client._http_client.request.call_args.kwargs["json"]
            assert body["fields"] == {"Name": "Ada"}

    async def test_typecast_off_by_default(
        self,
        success_response: Response,
    ) -> None:
        async with make_mock_client([success_response]) as client:
            table = Table(client, BASE_ID, TABLE_NAME)
            await table.create({"Name": "Ada"})

            assert isinstance(client._http_client.request, AsyncMock)
            body = client._http_client.request.call_args.kwargs["json"]
            assert "typecast" not in body

    async def test_typecast_true(
        self,
        success_response: Response,
    ) -> None:
        async with make_mock_client([success_response]) as client:
            table = Table(client, BASE_ID, TABLE_NAME)
            await table.create(
                {"Name": "Ada"},
                typecast=True,
            )

            assert isinstance(client._http_client.request, AsyncMock)
            body = client._http_client.request.call_args.kwargs["json"]
            assert body["typecast"] is True


class TestBatchCreate:
    async def test_wraps_in_fields(self) -> None:
        """batch_create should wrap each field dict in {"fields": ...}."""
        page_json: dict[str, JsonValue] = {"records": [RECORD_JSON]}
        async with make_mock_client([make_response(200, page_json)]) as client:
            table = Table(client, BASE_ID, TABLE_NAME)
            await table.batch_create([{"Name": "Ada"}])

            assert isinstance(client._http_client.request, AsyncMock)
            body = client._http_client.request.call_args.kwargs["json"]
            assert body["records"] == [
                {"fields": {"Name": "Ada"}},
            ]

    async def test_empty_input(self) -> None:
        async with make_mock_client([]) as client:
            table = Table(client, BASE_ID, TABLE_NAME)
            results = await table.batch_create([])

            assert results == []
            assert isinstance(client._http_client.request, AsyncMock)
            assert client._http_client.request.call_count == 0


class TestGet:
    async def test_returns_record(
        self,
        success_response: Response,
    ) -> None:
        async with make_mock_client([success_response]) as client:
            table = Table(client, BASE_ID, TABLE_NAME)
            record = await table.get("rec001")

        assert record.id == "rec001"
        assert record.fields["Name"] == "Ada"
        assert isinstance(record.created_time, datetime)


class TestAll:
    async def test_single_page(self) -> None:
        page_json: dict[str, JsonValue] = {
            "records": [RECORD_JSON],
            "offset": None,
        }
        async with make_mock_client([make_response(200, page_json)]) as client:
            table = Table(client, BASE_ID, TABLE_NAME)
            records = await table.all(
                formula="{Status}='Active'",
            )

        assert len(records) == 1
        assert records[0].id == "rec001"

    async def test_pagination(self) -> None:
        rec2 = {**RECORD_JSON, "id": "rec002"}
        page1: dict[str, JsonValue] = {
            "records": [RECORD_JSON],
            "offset": "itr_page2",
        }
        page2: dict[str, JsonValue] = {
            "records": [rec2],
            "offset": None,
        }
        responses = [make_response(200, page1), make_response(200, page2)]
        async with make_mock_client(responses) as client:
            table = Table(client, BASE_ID, TABLE_NAME)
            records = await table.all()

        assert len(records) == 2
        assert records[0].id == "rec001"
        assert records[1].id == "rec002"

    async def test_passes_formula_and_fields(self) -> None:
        page_json: dict[str, JsonValue] = {
            "records": [RECORD_JSON],
            "offset": None,
        }
        async with make_mock_client([make_response(200, page_json)]) as client:
            table = Table(client, BASE_ID, TABLE_NAME)
            await table.all(
                formula="{Status}='Active'",
                fields=["Name"],
                max_records=50,
            )

            assert isinstance(client._http_client.request, AsyncMock)
            call_kwargs = client._http_client.request.call_args.kwargs
            params = call_kwargs["params"]
            assert "filterByFormula" in str(params)
            assert "maxRecords" in str(params)


class TestUpdate:
    async def test_sends_patch(
        self,
        success_response: Response,
    ) -> None:
        async with make_mock_client([success_response]) as client:
            table = Table(client, BASE_ID, TABLE_NAME)
            record = await table.update(
                "rec001",
                {"Status": "Done"},
            )

            assert record.id == "rec001"
            assert isinstance(client._http_client.request, AsyncMock)
            assert client._http_client.request.call_args.args[0] == "PATCH"


class TestBatchUpdate:
    async def test_chunks_into_batches(self) -> None:
        """12 records should be split into 2 requests (10 + 2)."""
        updates = [UpdateRecord(id=f"rec{i:03d}", fields={"n": i}) for i in range(12)]
        page_json: dict[str, JsonValue] = {
            "records": [RECORD_JSON],
        }
        responses = [make_response(200, page_json)] * 2
        async with make_mock_client(responses) as client:
            table = Table(client, BASE_ID, TABLE_NAME)
            await table.batch_update(updates)

            mock_request = client._http_client.request
            assert isinstance(mock_request, AsyncMock)
            assert mock_request.call_count == 2
            first_body = mock_request.call_args_list[0].kwargs["json"]
            assert len(first_body["records"]) == 10
            second_body = mock_request.call_args_list[1].kwargs["json"]
            assert len(second_body["records"]) == 2

    async def test_empty_input(self) -> None:
        async with make_mock_client([]) as client:
            table = Table(client, BASE_ID, TABLE_NAME)
            results = await table.batch_update([])

            assert results == []
            assert isinstance(client._http_client.request, AsyncMock)
            assert client._http_client.request.call_count == 0


class TestDelete:
    async def test_returns_deleted(self) -> None:
        deleted_json = {"id": "rec001", "deleted": True}
        async with make_mock_client(
            [make_response(200, deleted_json)],
        ) as client:
            table = Table(client, BASE_ID, TABLE_NAME)
            result = await table.delete("rec001")

        assert result.id == "rec001"
        assert result.deleted is True


class TestBatchDelete:
    async def test_returns_deleted(self) -> None:
        deleted_json: dict[str, JsonValue] = {
            "records": [{"id": "rec001", "deleted": True}],
        }
        async with make_mock_client([make_response(200, deleted_json)]) as client:
            table = Table(client, BASE_ID, TABLE_NAME)
            results = await table.batch_delete(["rec001"])

        assert len(results) == 1
        assert results[0].deleted is True

    async def test_empty_input(self) -> None:
        async with make_mock_client([]) as client:
            table = Table(client, BASE_ID, TABLE_NAME)
            results = await table.batch_delete([])

            assert results == []
            assert isinstance(client._http_client.request, AsyncMock)
            assert client._http_client.request.call_count == 0


class TestSchema:
    async def test_returns_table_schema(self) -> None:
        async with make_mock_client([make_response(200, TABLES_JSON)]) as client:
            table = Table(client, BASE_ID, TABLE_NAME)
            schema = await table.schema()

        assert schema.id == "tbl001"
        assert schema.name == TABLE_NAME
        assert len(schema.fields) == 1
        assert schema.fields[0].name == "Name"

    async def test_table_not_found_raises(self) -> None:
        empty_tables: dict[str, JsonValue] = {"tables": []}
        async with make_mock_client([make_response(200, empty_tables)]) as client:
            table = Table(client, BASE_ID, TABLE_NAME)
            with pytest.raises(ValueError, match="not found"):
                await table.schema()


class TestEnsureFields:
    async def test_creates_missing_fields(self) -> None:
        new_field_json = {
            "id": "fld002",
            "name": "Status",
            "type": "singleSelect",
        }
        responses = [
            make_response(200, TABLES_JSON),
            make_response(200, new_field_json),
        ]
        async with make_mock_client(responses) as client:
            table = Table(client, BASE_ID, TABLE_NAME)
            results = await table.ensure_fields(
                {
                    "Name": FieldSpec(type="singleLineText"),
                    "Status": FieldSpec(type="singleSelect"),
                }
            )

        assert results["Name"] is False
        assert results["Status"] is True

    async def test_all_fields_exist(self) -> None:
        """When all fields exist, no create_field calls should be made."""
        async with make_mock_client([make_response(200, TABLES_JSON)]) as client:
            table = Table(client, BASE_ID, TABLE_NAME)
            results = await table.ensure_fields(
                {"Name": FieldSpec(type="singleLineText")}
            )

            assert results["Name"] is False
            assert isinstance(client._http_client.request, AsyncMock)
            # Only one request (schema), no create_field
            assert client._http_client.request.call_count == 1


class TestResolveTableId:
    async def test_caches_table_id(self) -> None:
        """Result should be cached for subsequent calls."""
        async with make_mock_client(
            [
                make_response(200, TABLES_JSON),
            ]
        ) as client:
            table = Table(client, BASE_ID, TABLE_NAME)
            id1 = await table._resolve_table_id()
            id2 = await table._resolve_table_id()

            assert id1 == "tbl001"
            assert id2 == "tbl001"
            assert isinstance(client._http_client.request, AsyncMock)
            # Only one HTTP request despite two calls
            assert client._http_client.request.call_count == 1
