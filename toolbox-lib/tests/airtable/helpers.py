from collections.abc import AsyncGenerator, Iterable
from contextlib import asynccontextmanager
from typing import cast
from unittest.mock import patch

from httpx import Request, Response
from tenacity import Retrying, wait_none

from toolbox.airtable import AirtableClient, JsonValue

FAKE_TOKEN = "abc123"


def make_response(
    status_code: int,
    json: JsonValue = None,
) -> Response:
    return Response(
        status_code,
        json=json,
        request=Request("GET", "https://fake"),
    )


def make_ok_response() -> Response:
    return make_response(
        200,
        json={
            "id": "rec001",
            "createdTime": "2026-01-01T00:00:00.000Z",
            "fields": {"Name": "Ada", "Status": "Active"},
        },
    )


@asynccontextmanager
async def make_mock_client(
    request_side_effect: Iterable[Response],
) -> AsyncGenerator[AirtableClient]:
    async with AirtableClient(timeout=5.0, token=FAKE_TOKEN) as client:
        with patch.object(
            client._http_client, "request", side_effect=request_side_effect
        ):
            retry = cast(
                Retrying,
                client.request.retry,  # pyright:ignore[reportAttributeAccessIssue]
            )
            retry.wait = wait_none()
            yield client
