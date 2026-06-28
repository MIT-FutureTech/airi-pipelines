import httpx

from toolbox.airtable.data_types import Attachment


async def download_attachment(
    client: httpx.AsyncClient,
    attachment: Attachment,
) -> bytes:
    """Download an attachment's bytes from its Airtable URL.

    The URL is a temporary signed link that expires shortly after the record
    was fetched. The URL needs no Airtable authentication, so pass a plain httpx
    client rather than an AirtableClient.
    """
    response = await client.get(attachment.url)
    response.raise_for_status()
    return response.content
