import asyncio
import logging
from collections.abc import (
    AsyncGenerator,
    AsyncIterable,
    AsyncIterator,
    Awaitable,
    Callable,
    Iterable,
    Sized,
)
from typing import Concatenate, NoReturn

import tqdm


class _Sentinel:
    pass


class _Failure:
    exception: BaseException

    def __init__(self, exception: BaseException) -> None:
        self.exception = exception


_DONE = _Sentinel()
logger = logging.getLogger(__name__)


class ConcurrentMap:
    """Dispatcher for mapping async function over an iterable.

    Items are consumed lazily from the input iterable, and results are yielded
    as they complete (not necessarily in input order).

    Enable progress reporting by setting `progress_description`. If the iterable
    is sized, the total number of items will be determined automatically.
    Otherwise, set `progress_total`.

    Usage:

        mapper = ConcurrentMap(max_concurrency=5)
        for result in mapper.map(my_func, range(10)):
            print(result)
    """

    max_concurrency: int
    progress_description: str | None
    progress_total: int | None

    def __init__(
        self,
        *,
        max_concurrency: int,
        progress_description: str | None = None,
        progress_total: int | None = None,
    ) -> None:
        self.max_concurrency = max_concurrency
        self.progress_description = progress_description
        self.progress_total = progress_total

    async def map[T, **P, R](
        self,
        items: AsyncIterable[T] | Iterable[T],
        func: Callable[Concatenate[T, P], Awaitable[R]],
        /,
        *args: P.args,
        **kwargs: P.kwargs,
    ) -> AsyncGenerator[R]:
        async def bound(item: T) -> R:
            return await func(item, *args, **kwargs)

        in_queue: asyncio.Queue[T | _Sentinel] = asyncio.Queue(
            maxsize=self.max_concurrency
        )
        out_queue: asyncio.Queue[R | _Sentinel | _Failure] = asyncio.Queue()
        progress: tqdm.tqdm[NoReturn] | None = None
        progress_total = self.progress_total
        if self.progress_description:
            if progress_total is None and isinstance(items, Sized):
                progress_total = len(items)
            progress = tqdm.tqdm(desc=self.progress_description, total=progress_total)

        producer = asyncio.create_task(
            _producer(
                items=items,
                in_queue=in_queue,
                max_concurrency=self.max_concurrency,
            ),
        )
        workers = [
            asyncio.create_task(
                _worker(in_queue=in_queue, func=bound, out_queue=out_queue)
            )
            for _ in range(self.max_concurrency)
        ]

        try:
            finished_worker_count = 0
            while finished_worker_count < self.max_concurrency:
                item = await out_queue.get()
                if isinstance(item, _Sentinel):
                    finished_worker_count += 1
                elif isinstance(item, _Failure):
                    raise item.exception
                else:
                    if progress is not None:
                        progress.update()
                    yield item
        except:
            logger.info("Cancelling workers")
            raise
        finally:
            if progress is not None:
                progress.close()
            producer.cancel()
            for w in workers:
                w.cancel()
            await asyncio.gather(producer, *workers, return_exceptions=True)


async def _producer[T](
    items: AsyncIterable[T] | Iterable[T],
    in_queue: asyncio.Queue[T | _Sentinel],
    max_concurrency: int,
) -> None:
    async for item in _to_async_iterable(items):
        await in_queue.put(item)
    for _ in range(max_concurrency):
        await in_queue.put(_DONE)


async def _worker[T, R](
    in_queue: asyncio.Queue[T | _Sentinel],
    func: Callable[[T], Awaitable[R]],
    out_queue: asyncio.Queue[R | _Sentinel | _Failure],
) -> None:
    try:
        while True:
            item = await in_queue.get()
            if isinstance(item, _Sentinel):
                return
            result = await func(item)
            await out_queue.put(result)
    except Exception as e:
        await out_queue.put(_Failure(e))
    finally:
        await out_queue.put(_DONE)


async def _to_async_iterable[T](
    items: AsyncIterable[T] | Iterable[T],
) -> AsyncIterator[T]:
    if isinstance(items, AsyncIterable):
        async for item in items:
            yield item
    else:
        for item in items:
            yield item
