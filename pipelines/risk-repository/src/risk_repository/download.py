import logging
from datetime import UTC, datetime
from pathlib import Path

import httpx
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class DownloadFailure(BaseModel):
    readable_id: str
    url: str | None
    reason: str
    details: str | None
    timestamp: datetime


def make_http_client() -> httpx.AsyncClient:
    return httpx.AsyncClient(
        follow_redirects=True,
        headers={
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:149.0) Gecko/20100101 Firefox/149.0"
        },
    )


async def download_pdf(
    *,
    url: str,
    cache_dir: Path,
    readable_id: str,
    client: httpx.AsyncClient,
) -> Path | None:
    cached = cache_dir / f"{readable_id}.pdf"
    if cached.exists():
        logger.debug(f"Cache hit: {cached}")
        return cached

    fetch_url = url.replace("https://arxiv.org/abs/", "https://arxiv.org/pdf/")
    response = await client.get(fetch_url)
    if response.status_code in {403, 404}:
        logger.warning(
            f"Skipping {readable_id} due to fetch error: {response.status_code}"
        )
        logger.debug(f"Request for {fetch_url} returned response\n{response.text}")
        record_failure(
            cache_dir=cache_dir,
            readable_id=readable_id,
            url=url,
            reason=f"HTTP {response.status_code}",
            details=response.text,
        )
        return None
    response.raise_for_status()
    content_type = response.headers.get("content-type", "").split(";")[0].strip()
    if content_type != "application/pdf":
        logger.warning(f"Skipping {readable_id}: expected PDF, got {content_type}")
        record_failure(
            cache_dir=cache_dir,
            readable_id=readable_id,
            url=url,
            reason=f"expected PDF, got {content_type}",
            details=None,
        )
        return None

    cached.write_bytes(response.content)
    clear_failure(cache_dir=cache_dir, readable_id=readable_id)
    logger.info(f"Downloaded {url} -> {cached}")
    return cached


def record_failure(
    *,
    cache_dir: Path,
    readable_id: str,
    url: str | None,
    reason: str,
    details: str | None,
) -> None:
    failure = DownloadFailure(
        readable_id=readable_id,
        url=url,
        reason=reason,
        details=details,
        timestamp=datetime.now(UTC),
    )
    _failure_path(cache_dir, readable_id).write_text(failure.model_dump_json(indent=2))


def clear_failure(*, cache_dir: Path, readable_id: str) -> None:
    path = _failure_path(cache_dir, readable_id)
    if path.exists():
        path.unlink()


def _failure_path(cache_dir: Path, readable_id: str) -> Path:
    return cache_dir / f"{readable_id}.failed.json"
