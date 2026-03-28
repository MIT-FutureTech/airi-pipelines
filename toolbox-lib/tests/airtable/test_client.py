from unittest.mock import AsyncMock

import pytest
from httpx import HTTPStatusError

from .helpers import make_mock_client, make_ok_response, make_response

pytestmark = [pytest.mark.asyncio]


class TestRetry:
    async def test_retries_on_429(self) -> None:
        """Should retry on 429 and succeed on the next attempt."""
        async with make_mock_client([make_response(429), make_ok_response()]) as client:
            resp = await client.request(
                "appXXX",
                "GET",
                "https://fake",
            )
            assert resp.status_code == 200
            assert isinstance(client._http_client.request, AsyncMock)
            assert client._http_client.request.call_count == 2

    async def test_no_retry_on_400(self) -> None:
        """Non-retryable errors should raise immediately."""
        async with make_mock_client([make_response(400)]) as client:
            with pytest.raises(HTTPStatusError):
                await client.request(
                    "appXXX",
                    "GET",
                    "https://fake",
                )
            assert isinstance(client._http_client.request, AsyncMock)
            assert client._http_client.request.call_count == 1
