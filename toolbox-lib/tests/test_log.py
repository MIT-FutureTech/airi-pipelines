import asyncio
import io
import logging
from collections.abc import Iterator

import pytest

from toolbox.log import (
    _LogContextFilter,
    install_log_context_filter,
    log_context,
)


@pytest.fixture
def logger() -> logging.Logger:
    logger = logging.getLogger(__name__)
    logger.handlers.clear()
    logger.propagate = False
    logger.setLevel(logging.DEBUG)
    return logger


@pytest.fixture
def stream(logger: logging.Logger) -> Iterator[io.StringIO]:
    stream = io.StringIO()
    handler = logging.StreamHandler(stream)
    handler.setFormatter(logging.Formatter("{message}", style="{"))
    handler.addFilter(_LogContextFilter())
    logger.addHandler(handler)
    try:
        yield stream
    finally:
        logger.handlers.clear()


class TestLogContext:
    def test_no_context_leaves_message_unchanged(
        self,
        logger: logging.Logger,
        stream: io.StringIO,
    ) -> None:
        logger.info("hello")
        assert stream.getvalue().strip() == "hello"

    def test_appends_single_field(
        self,
        logger: logging.Logger,
        stream: io.StringIO,
    ) -> None:
        with log_context(rec_id="R-1"):
            logger.info("processing")
        assert stream.getvalue().strip() == "processing [rec_id=R-1]"

    def test_appends_multiple_fields(
        self,
        logger: logging.Logger,
        stream: io.StringIO,
    ) -> None:
        with log_context(rec_id="R-1", attempt=2):
            logger.info("processing")
        assert stream.getvalue().strip() == "processing [rec_id=R-1 attempt=2]"

    def test_nested_contexts_merge(
        self,
        logger: logging.Logger,
        stream: io.StringIO,
    ) -> None:
        with log_context(rec_id="R-1"), log_context(item_id="X-1"):
            logger.info("processing")
        assert stream.getvalue().strip() == "processing [rec_id=R-1 item_id=X-1]"

    def test_inner_context_overrides_outer(
        self,
        logger: logging.Logger,
        stream: io.StringIO,
    ) -> None:
        with log_context(stage="first"), log_context(stage="second"):
            logger.info("running")
        assert stream.getvalue().strip() == "running [stage=second]"

    def test_context_does_not_leak_after_exit(
        self,
        logger: logging.Logger,
        stream: io.StringIO,
    ) -> None:
        with log_context(rec_id="R-1"):
            logger.info("inside")
        logger.info("outside")
        assert stream.getvalue().splitlines() == [
            "inside [rec_id=R-1]",
            "outside",
        ]

    def test_preserves_percent_style_formatting(
        self,
        logger: logging.Logger,
        stream: io.StringIO,
    ) -> None:
        with log_context(rec_id="R-1"):
            logger.info("count=%d", 42)
        assert stream.getvalue().strip() == "count=42 [rec_id=R-1]"

    async def test_concurrent_tasks_do_not_leak_fields(
        self,
        logger: logging.Logger,
        stream: io.StringIO,
    ) -> None:

        async def work(rec_id: str) -> None:
            with log_context(rec_id=rec_id):
                await asyncio.sleep(0.01)
                logger.info("done")

        await asyncio.gather(work("A"), work("B"), work("C"))
        assert sorted(stream.getvalue().splitlines()) == [
            "done [rec_id=A]",
            "done [rec_id=B]",
            "done [rec_id=C]",
        ]


class TestInstallLogContextFilter:
    def test_attaches_filter_to_each_root_handler(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        root = logging.getLogger()
        handlers = [logging.NullHandler(), logging.NullHandler()]
        monkeypatch.setattr(root, "handlers", handlers)
        install_log_context_filter()
        for handler in handlers:
            assert any(isinstance(f, _LogContextFilter) for f in handler.filters)
