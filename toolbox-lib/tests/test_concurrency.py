import asyncio
from collections.abc import AsyncIterator

import pytest

from toolbox.concurrency import concurrent_map


async def slow_double(x: int) -> int:
    await asyncio.sleep(0.05)
    return x * 2


async def failing(x: int) -> int:
    if x == 3:
        raise ValueError("bad item")
    return x


class TestConcurrentMap:
    async def test_processes_all_items(self) -> None:
        results = [
            r async for r in concurrent_map(range(20), slow_double, max_concurrency=5)
        ]
        assert sorted(results) == [x * 2 for x in range(20)]

    async def test_respects_concurrency_limit(self) -> None:
        peak = 0
        current = 0
        lock = asyncio.Lock()

        async def track_concurrency(x: int) -> int:
            nonlocal peak, current
            async with lock:
                current += 1
                peak = max(peak, current)
            await asyncio.sleep(0.05)
            async with lock:
                current -= 1
            return x

        results = [
            r
            async for r in concurrent_map(
                range(20), track_concurrency, max_concurrency=3
            )
        ]
        assert len(results) == 20
        assert peak <= 3

    async def test_is_lazy(self) -> None:
        """Items should not all be consumed upfront."""
        consumed_count = 0

        async def counting_source() -> AsyncIterator[int]:
            nonlocal consumed_count
            for i in range(100):
                consumed_count += 1
                yield i

        count = 0
        async for _ in concurrent_map(
            counting_source(), slow_double, max_concurrency=3
        ):
            count += 1
            if count == 5:
                break

        # With max_concurrency=3 , we should have consumed far fewer than all 100 items
        assert consumed_count < 20

    async def test_accepts_sync_iterable(self) -> None:
        results = [
            r async for r in concurrent_map([1, 2, 3], slow_double, max_concurrency=2)
        ]
        assert sorted(results) == [2, 4, 6]

    async def test_accepts_async_iterable(self) -> None:
        async def async_items() -> AsyncIterator[int]:
            for i in [1, 2, 3]:
                yield i

        results = [
            r
            async for r in concurrent_map(async_items(), slow_double, max_concurrency=2)
        ]
        assert sorted(results) == [2, 4, 6]

    async def test_empty_input(self) -> None:
        results = [r async for r in concurrent_map([], slow_double, max_concurrency=5)]
        assert results == []

    async def test_single_concurrency(self) -> None:
        results = [
            r async for r in concurrent_map(range(5), slow_double, max_concurrency=1)
        ]
        # With concurrency=1, items should be processed in order
        assert results == [0, 2, 4, 6, 8]

    async def test_propagates_exception(self) -> None:
        with pytest.raises(ValueError, match="bad item") as err_info:
            async for _ in concurrent_map(range(10), failing, max_concurrency=2):
                pass

        # Assert that traceback points to original raise in failing()
        bottom_frame = err_info.traceback[-1]
        assert bottom_frame.name == "failing"
        assert str(bottom_frame.statement).strip() == 'raise ValueError("bad item")'
