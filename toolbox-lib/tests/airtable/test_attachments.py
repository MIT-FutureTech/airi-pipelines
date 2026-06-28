from unittest.mock import AsyncMock, patch

import httpx
import pytest

from toolbox.airtable import Attachment, download_attachment

ATTACHMENT = Attachment(
    id="att001",
    url="https://example.com/file.pdf",
    filename="file.pdf",
)


class TestDownloadAttachment:
    async def test_returns_bytes(self) -> None:
        response = httpx.Response(
            200,
            content=b"%PDF-1.4 body",
            request=httpx.Request("GET", ATTACHMENT.url),
        )
        async with httpx.AsyncClient() as client:
            with patch.object(
                client, "get", AsyncMock(return_value=response)
            ) as mock_get:
                data = await download_attachment(client, ATTACHMENT)

        assert data == b"%PDF-1.4 body"
        mock_get.assert_awaited_once_with(ATTACHMENT.url)

    async def test_raises_on_error_status(self) -> None:
        response = httpx.Response(
            404,
            request=httpx.Request("GET", ATTACHMENT.url),
        )
        async with httpx.AsyncClient() as client:
            with patch.object(client, "get", AsyncMock(return_value=response)):
                with pytest.raises(httpx.HTTPStatusError):
                    await download_attachment(client, ATTACHMENT)
