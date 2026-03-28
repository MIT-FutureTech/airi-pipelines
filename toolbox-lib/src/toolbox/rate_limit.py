import asyncio
import time


class RateLimiter:
    """Asynchronous rate limiter

    Usage:
        limiter = AsyncRateLimiter(requests_per_second=10.0)
        for item in items:
            await limiter.acquire()
            api.submit(item)
    """

    _min_interval_seconds: float
    _lock: asyncio.Lock
    _last_acquire_time_monotonic: float

    def __init__(self, requests_per_second: float) -> None:
        self._min_interval_seconds = 1.0 / requests_per_second
        self._lock = asyncio.Lock()
        self._last_acquire_time_monotonic = 0.0

    async def acquire(self) -> None:
        """Block until a new request would not exceed the rate limit."""
        async with self._lock:
            now = time.monotonic()
            elapsed_seconds = now - self._last_acquire_time_monotonic
            if elapsed_seconds < self._min_interval_seconds:
                await asyncio.sleep(self._min_interval_seconds - elapsed_seconds)
            self._last_acquire_time_monotonic = time.monotonic()
