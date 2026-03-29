import logging
from collections.abc import AsyncIterator, Sequence

from httpx import QueryParams, Response

from toolbox.airtable.client import Client
from toolbox.airtable.data_types import (
    DeletedRecord,
    DeletedRecordList,
    FieldSchema,
    FieldSpec,
    JsonObject,
    JsonValue,
    Record,
    RecordList,
    TableSchema,
    TablesResponse,
    UpdateRecord,
)

API_URL = "https://api.airtable.com/v0"
META_URL = f"{API_URL}/meta/bases"
BATCH_SIZE = 10  # Constraint imposed by Airtable API
logger = logging.getLogger(__name__)


class Table:
    """Operations on a single Airtable table."""

    _client: Client
    _base_id: str
    _table_name: str
    _url: str
    _table_id: str | None

    def __init__(
        self,
        client: Client,
        base_id: str,
        table_name: str,
    ) -> None:
        self._client = client
        self._base_id = base_id
        self._table_name = table_name
        self._url = f"{API_URL}/{base_id}/{table_name}"
        self._table_id = None

    async def create(
        self,
        fields: JsonObject,
        *,
        typecast: bool = False,
    ) -> Record:
        """Create a single record.

        When typecast is True, Airtable will attempt best-effort automatic conversion
        from string values.
        """
        body: dict[str, JsonValue] = {"fields": fields}
        if typecast:
            body["typecast"] = True
        resp = await self._request("POST", self._url, body=body)
        return Record.model_validate(resp.json())

    async def batch_create(
        self,
        records: Sequence[JsonObject],
        *,
        typecast: bool = False,
    ) -> list[Record]:
        """Create multiple records from field dicts.

        Each element is a field dict, e.g. `{"Name": "Ada"}`.

        When typecast is True, Airtable will attempt best-effort automatic conversion
        from string values.
        """
        results: list[Record] = []
        for i in range(0, len(records), BATCH_SIZE):
            chunk = records[i : i + BATCH_SIZE]
            body: dict[str, JsonValue] = {
                "records": [{"fields": r} for r in chunk],
            }
            if typecast:
                body["typecast"] = True
            resp = await self._request(
                "POST",
                self._url,
                body=body,
            )
            page = RecordList.model_validate(resp.json())
            results.extend(page.records)
        return results

    async def get(self, record_id: str) -> Record:
        """Retrieve a single record by ID."""
        resp = await self._request(
            "GET",
            f"{self._url}/{record_id}",
        )
        return Record.model_validate(resp.json())

    async def all(
        self,
        *,
        formula: str | None = None,
        fields: list[str] | None = None,
        max_records: int | None = None,
        sort: list[tuple[str, str]] | None = None,
    ) -> list[Record]:
        """Fetch all matching records.

        Prefer iterate() if the number of records is large.
        """
        return [
            record
            async for record in self.iterate(
                formula=formula,
                fields=fields,
                max_records=max_records,
                sort=sort,
            )
        ]

    async def iterate(
        self,
        *,
        formula: str | None = None,
        fields: list[str] | None = None,
        max_records: int | None = None,
        page_size: int | None = None,
        sort: list[tuple[str, str]] | None = None,
    ) -> AsyncIterator[Record]:
        """Iterate over matching records."""
        offset: str | None = None
        while True:
            params = _build_list_params(
                formula=formula,
                fields=fields,
                max_records=max_records,
                page_size=page_size,
                sort=sort,
                offset=offset,
            )
            resp = await self._request(
                "GET",
                self._url,
                params=params,
            )
            page = RecordList.model_validate(resp.json())
            for record in page.records:
                yield record
            offset = page.offset
            if offset is None:
                break

    async def update(
        self,
        record_id: str,
        fields: JsonObject,
        *,
        typecast: bool = False,
    ) -> Record:
        """Update a single record.

        When typecast is True, Airtable will attempt best-effort automatic conversion
        from string values.
        """
        body: dict[str, JsonValue] = {"fields": fields}
        if typecast:
            body["typecast"] = True
        resp = await self._request(
            "PATCH",
            f"{self._url}/{record_id}",
            body=body,
        )
        return Record.model_validate(resp.json())

    async def batch_update(
        self,
        records: Sequence[UpdateRecord],
        *,
        typecast: bool = False,
    ) -> list[Record]:
        """Update multiple records.

        When typecast is True, Airtable will attempt best-effort automatic conversion
        from string values.
        """
        results: list[Record] = []
        for i in range(0, len(records), BATCH_SIZE):
            chunk = records[i : i + BATCH_SIZE]
            payload = [r.model_dump() for r in chunk]
            body: dict[str, JsonValue] = {"records": payload}
            if typecast:
                body["typecast"] = True
            resp = await self._request(
                "PATCH",
                self._url,
                body=body,
            )
            page = RecordList.model_validate(resp.json())
            results.extend(page.records)
        return results

    async def delete(self, record_id: str) -> DeletedRecord:
        """Delete a single record."""
        resp = await self._request(
            "DELETE",
            f"{self._url}/{record_id}",
        )
        return DeletedRecord.model_validate(resp.json())

    async def batch_delete(
        self,
        record_ids: Sequence[str],
    ) -> list[DeletedRecord]:
        """Delete multiple records."""
        results: list[DeletedRecord] = []
        for i in range(0, len(record_ids), BATCH_SIZE):
            chunk = record_ids[i : i + BATCH_SIZE]
            params = QueryParams()
            for rid in chunk:
                params = params.add("records[]", rid)
            resp = await self._request(
                "DELETE",
                self._url,
                params=params,
            )
            page = DeletedRecordList.model_validate(resp.json())
            results.extend(page.records)
        return results

    async def schema(self) -> TableSchema:
        """Fetch the current table schema from the Metadata API."""
        resp = await self._request(
            "GET",
            f"{META_URL}/{self._base_id}/tables",
        )
        data = TablesResponse.model_validate(resp.json())
        for t in data.tables:
            if t.name == self._table_name or t.id == self._table_name:
                self._table_id = t.id
                return t

        msg = f"Table {self._table_name!r} not found in base {self._base_id}"
        raise ValueError(msg)

    async def create_field(
        self,
        name: str,
        field_type: str,
        *,
        options: JsonObject | None = None,
        description: str | None = None,
    ) -> FieldSchema:
        """Create a new field in the table via the Metadata API."""
        table_id = await self._resolve_table_id()
        body: dict[str, JsonValue] = {
            "name": name,
            "type": field_type,
        }
        if options is not None:
            body["options"] = options
        if description is not None:
            body["description"] = description

        resp = await self._request(
            "POST",
            f"{META_URL}/{self._base_id}/tables/{table_id}/fields",
            body=body,
        )
        return FieldSchema.model_validate(resp.json())

    async def ensure_fields(
        self,
        specs: dict[str, FieldSpec],
    ) -> dict[str, bool]:
        """Ensure fields exist, creating any that are missing.

        Returns a mapping of field name to whether it was created
        (True) or already existed (False).
        """
        current = await self.schema()
        existing = {f.name for f in current.fields}

        results: dict[str, bool] = {}
        for name, spec in specs.items():
            if name in existing:
                results[name] = False
            else:
                _ = await self.create_field(
                    name,
                    spec.type,
                    options=spec.options,
                    description=spec.description,
                )
                results[name] = True
                logger.info(
                    "Created Airtable field %r (type=%s)",
                    name,
                    spec.type,
                )

        return results

    async def _request(
        self,
        method: str,
        url: str,
        *,
        params: QueryParams | None = None,
        body: JsonObject | None = None,
    ) -> Response:
        return await self._client.request(
            self._base_id,
            method,
            url,
            params=params,
            body=body,
        )

    async def _resolve_table_id(self) -> str:
        """Resolve the table name to a table ID via the Metadata API.

        The result is cached so subsequent calls do not hit the network.
        """
        if self._table_id is not None:
            return self._table_id

        resp = await self._request(
            "GET",
            f"{META_URL}/{self._base_id}/tables",
        )
        data = TablesResponse.model_validate(resp.json())
        for t in data.tables:
            if t.name == self._table_name or t.id == self._table_name:
                self._table_id = t.id
                return t.id

        msg = f"Table {self._table_name!r} not found in base {self._base_id}"
        raise ValueError(msg)


def _build_list_params(
    *,
    formula: str | None = None,
    fields: list[str] | None = None,
    max_records: int | None = None,
    page_size: int | None = None,
    sort: list[tuple[str, str]] | None = None,
    offset: str | None = None,
) -> QueryParams | None:
    """Build query parameters for the list-records endpoint."""
    params = QueryParams()
    if formula is not None:
        params = params.add("filterByFormula", formula)
    if fields is not None:
        for f in fields:
            params = params.add("fields[]", f)
    if max_records is not None:
        params = params.add("maxRecords", str(max_records))
    if page_size is not None:
        params = params.add("pageSize", str(page_size))
    if sort is not None:
        for i, (field_name, direction) in enumerate(sort):
            params = params.add(
                f"sort[{i}][field]",
                field_name,
            )
            params = params.add(
                f"sort[{i}][direction]",
                direction,
            )
    if offset is not None:
        params = params.add("offset", offset)
    if not params:
        return None
    return params
