import asyncio
import time

import pytest

from toolbox.rate_limit import RateLimiter

pytestmark = [pytest.mark.asyncio]


class TestRateLimiter:
    async def test_acquire_spaces_requests(self) -> None:
        """Consecutive acquires should be spaced by at least the min interval."""
        limiter = RateLimiter(requests_per_second=50.0)
        min_interval = 1.0 / 50.0

        start = time.monotonic()
        await limiter.acquire()
        await limiter.acquire()
        await limiter.acquire()
        elapsed = time.monotonic() - start

        # 3 acquires = 2 intervals between them
        assert elapsed >= min_interval * 2

    async def test_concurrent_acquire_serializes(self) -> None:
        """Multiple concurrent acquires for the same resource should serialize."""
        limiter = RateLimiter(requests_per_second=50.0)
        min_interval = 1.0 / 50.0
        timestamps: list[float] = []

        async def worker() -> None:
            await limiter.acquire()
            timestamps.append(time.monotonic())

        start = time.monotonic()
        await asyncio.gather(*[worker() for _ in range(5)])
        elapsed = time.monotonic() - start

        # 5 acquires on same resource = 4 intervals
        assert elapsed >= min_interval * 4
