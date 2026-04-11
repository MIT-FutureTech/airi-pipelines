import asyncio
import logging
from collections.abc import AsyncIterable, AsyncIterator, Awaitable, Callable, Iterable


class _Sentinel:
    pass


class _Failure:
    exception: BaseException

    def __init__(self, exception: BaseException) -> None:
        self.exception = exception


_DONE = _Sentinel()
logger = logging.getLogger(__name__)


async def concurrent_map[T, R](
    items: AsyncIterable[T] | Iterable[T],
    func: Callable[[T], Awaitable[R]],
    max_concurrency: int,
) -> AsyncIterator[R]:
    """Apply an async function to items with bounded concurrency.

    Items are consumed lazily from the input iterable, and results are yielded
    as they complete (not necessarily in input order).
    """
    in_queue: asyncio.Queue[T | _Sentinel] = asyncio.Queue(maxsize=max_concurrency)
    out_queue: asyncio.Queue[R | _Sentinel | _Failure] = asyncio.Queue()

    producer = asyncio.create_task(
        _producer(items=items, in_queue=in_queue, max_concurrency=max_concurrency),
    )
    workers = [
        asyncio.create_task(_worker(in_queue=in_queue, func=func, out_queue=out_queue))
        for _ in range(max_concurrency)
    ]

    try:
        finished_worker_count = 0
        while finished_worker_count < max_concurrency:
            item = await out_queue.get()
            if isinstance(item, _Sentinel):
                finished_worker_count += 1
            elif isinstance(item, _Failure):
                raise item.exception
            else:
                yield item
    finally:
        logger.info("Cancelling workers")
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
