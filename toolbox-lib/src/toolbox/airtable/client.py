import logging
import os
from types import TracebackType
from typing import Self

from httpx import AsyncClient, HTTPStatusError, QueryParams, Response
from tenacity import (
    after_log,
    retry,
    retry_if_exception,
    stop_after_attempt,
    wait_exponential,
)

from toolbox.airtable.data_types import JsonObject
from toolbox.rate_limit import RateLimiter

logger = logging.getLogger(__name__)

API_URL = "https://api.airtable.com/v0"
META_URL = f"{API_URL}/meta/bases"
RETRYABLE_STATUSES = frozenset({429, 502, 503, 504})
RATE_LIMIT_REQUESTS_PER_SECOND = 5.0  # Constraint imposed by Airtable API


def _is_retryable(exc: BaseException) -> bool:
    return (
        isinstance(exc, HTTPStatusError)
        and exc.response.status_code in RETRYABLE_STATUSES
    )


class Client:
    """Airtable API client with per-base rate limiting and retry.

    Usage:

        async with Client("pat...", timeout=30.0) as client:
            table = Table(client, "appXXX", "Records")
            records = await table.all(formula="{Status}='Active'")
    """

    _http_client: AsyncClient
    _rate_limiters: dict[str, RateLimiter]

    def __init__(
        self,
        *,
        timeout: float,
        token: str | None = None,
    ) -> None:
        if token is None:
            token = os.environ["AIRTABLE_TOKEN"]
        self._http_client = AsyncClient(
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            },
            timeout=timeout,
        )
        self._rate_limiters = {}

    @retry(
        retry=retry_if_exception(_is_retryable),
        wait=wait_exponential(multiplier=1, max=30),
        stop=stop_after_attempt(5),
        after=after_log(logger, logging.INFO),
        reraise=True,
    )
    async def request(
        self,
        base_id: str,
        method: str,
        url: str,
        *,
        params: QueryParams | None = None,
        body: JsonObject | None = None,
    ) -> Response:
        """Make a rate-limited HTTP request with retry on transient errors."""
        rate_limiter = self._rate_limiters.setdefault(
            base_id,
            RateLimiter(RATE_LIMIT_REQUESTS_PER_SECOND),
        )
        await rate_limiter.acquire()
        response = await self._http_client.request(
            method,
            url,
            params=params,
            json=body,
        )
        response.raise_for_status()
        return response

    async def close(self) -> None:
        await self._http_client.aclose()

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        await self.close()
