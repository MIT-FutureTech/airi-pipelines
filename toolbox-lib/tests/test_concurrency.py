import asyncio
from collections.abc import AsyncIterator
from unittest.mock import MagicMock, patch

import pytest

from toolbox.concurrency import ConcurrentMap


async def slow_double(x: int) -> int:
    await asyncio.sleep(0.05)
    return x * 2


async def failing(x: int) -> int:
    if x == 3:
        raise ValueError("bad item")
    return x


class TestConcurrentMap:
    async def test_processes_all_items(self) -> None:
        runner = ConcurrentMap(max_concurrency=5)
        results = [r async for r in runner.map(range(20), slow_double)]
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

        runner = ConcurrentMap(max_concurrency=3)
        results = [r async for r in runner.map(range(20), track_concurrency)]
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

        runner = ConcurrentMap(max_concurrency=3)
        count = 0
        async for _ in runner.map(counting_source(), slow_double):
            count += 1
            if count == 5:
                break

        # With max_concurrency=3 , we should have consumed far fewer than all 100 items
        assert consumed_count < 20

    async def test_accepts_sync_iterable(self) -> None:
        runner = ConcurrentMap(max_concurrency=2)
        results = [r async for r in runner.map([1, 2, 3], slow_double)]
        assert sorted(results) == [2, 4, 6]

    async def test_accepts_async_iterable(self) -> None:
        async def async_items() -> AsyncIterator[int]:
            for i in [1, 2, 3]:
                yield i

        runner = ConcurrentMap(max_concurrency=2)
        results = [r async for r in runner.map(async_items(), slow_double)]
        assert sorted(results) == [2, 4, 6]

    async def test_empty_input(self) -> None:
        runner = ConcurrentMap(max_concurrency=5)
        results = [r async for r in runner.map([], slow_double)]
        assert results == []

    async def test_single_concurrency(self) -> None:
        runner = ConcurrentMap(max_concurrency=1)
        results = [r async for r in runner.map(range(5), slow_double)]
        # With concurrency=1, items should be processed in order
        assert results == [0, 2, 4, 6, 8]

    async def test_propagates_exception(self) -> None:
        runner = ConcurrentMap(max_concurrency=2)
        with pytest.raises(ValueError, match="bad item") as err_info:
            async for _ in runner.map(range(10), failing):
                pass

        # Assert that traceback points to original raise in failing()
        bottom_frame = err_info.traceback[-1]
        assert bottom_frame.name == "failing"
        assert str(bottom_frame.statement).strip() == 'raise ValueError("bad item")'


class TestConcurrentMapProgress:
    @patch("toolbox.concurrency.tqdm.tqdm")
    async def test_updates_once_per_result(self, mock_tqdm_cls: MagicMock) -> None:
        progress_bar = mock_tqdm_cls.return_value
        items = list(range(10))
        runner = ConcurrentMap(max_concurrency=3, progress_description="test")
        async for _ in runner.map(items, slow_double):
            pass
        assert progress_bar.update.call_count == len(items)

    @patch("toolbox.concurrency.tqdm.tqdm")
    async def test_auto_detects_total_from_sized(
        self,
        mock_tqdm_cls: MagicMock,
    ) -> None:
        items = list(range(7))
        runner = ConcurrentMap(max_concurrency=3, progress_description="test")
        async for _ in runner.map(items, slow_double):
            pass
        mock_tqdm_cls.assert_called_once_with(desc="test", total=7)

    @patch("toolbox.concurrency.tqdm.tqdm")
    async def test_no_total_for_unsized_iterables(
        self,
        mock_tqdm_cls: MagicMock,
    ) -> None:
        items = (num for num in range(7))
        runner = ConcurrentMap(max_concurrency=3, progress_description="test")
        async for _ in runner.map(items, slow_double):
            pass
        mock_tqdm_cls.assert_called_once_with(desc="test", total=None)

    @patch("toolbox.concurrency.tqdm.tqdm")
    async def test_explicit_total_overrides_auto(
        self,
        mock_tqdm_cls: MagicMock,
    ) -> None:
        runner = ConcurrentMap(
            max_concurrency=3, progress_description="test", progress_total=99
        )
        async for _ in runner.map(list(range(5)), slow_double):
            pass
        mock_tqdm_cls.assert_called_once_with(desc="test", total=99)

    @patch("toolbox.concurrency.tqdm.tqdm")
    async def test_closed_on_completion(self, mock_tqdm_cls: MagicMock) -> None:
        progress_bar = mock_tqdm_cls.return_value
        runner = ConcurrentMap(max_concurrency=2, progress_description="test")
        async for _ in runner.map([1, 2], slow_double):
            pass
        progress_bar.close.assert_called_once()

    @patch("toolbox.concurrency.tqdm.tqdm")
    async def test_closed_on_exception(self, mock_tqdm_cls: MagicMock) -> None:
        progress_bar = mock_tqdm_cls.return_value
        runner = ConcurrentMap(max_concurrency=2, progress_description="test")
        with pytest.raises(ValueError, match="bad item"):
            async for _ in runner.map(range(10), failing):
                pass
        progress_bar.close.assert_called_once()

    @patch("toolbox.concurrency.tqdm.tqdm")
    async def test_closed_on_early_break(self, mock_tqdm_cls: MagicMock) -> None:
        progress_bar = mock_tqdm_cls.return_value
        count = 0
        runner = ConcurrentMap(max_concurrency=3, progress_description="test")
        generator = runner.map(range(100), slow_double)
        async for _ in generator:
            count += 1
            if count == 3:
                break
        await generator.aclose()
        progress_bar.close.assert_called_once()

    @patch("toolbox.concurrency.tqdm.tqdm")
    async def test_no_bar_without_description(self, mock_tqdm_cls: MagicMock) -> None:
        runner = ConcurrentMap(max_concurrency=1)
        async for _ in runner.map([1, 2], slow_double):
            pass
        mock_tqdm_cls.assert_not_called()
