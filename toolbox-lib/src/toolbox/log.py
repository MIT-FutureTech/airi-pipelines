import contextvars
import logging
from collections.abc import Iterable, Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import TextIO, override

from tqdm import tqdm


def configure_logging(
    level: int,
    *,
    filepath: Path | None = None,
    loggers_to_silence: Iterable[str] = (),
) -> None:
    """Configure log level, format and handlers.

    This must be called before any log messages are emitted.
    """
    handlers: list[logging.Handler] = [_TqdmStreamHandler()]
    if filepath is not None:
        handlers.append(logging.FileHandler(filepath, mode="a"))
    logging.basicConfig(
        handlers=handlers,
        style="{",
        format="{asctime:s} {levelname:7s} {name:s}:{lineno:d} {message:s}",
        datefmt="%Y-%m-%dT%H:%M:%S%z",
        level=level,
    )
    for logger_name in loggers_to_silence:
        logging.getLogger(logger_name).setLevel(level=logging.WARNING)


_log_context: contextvars.ContextVar[dict[str, object] | None] = contextvars.ContextVar(
    "_log_context", default=None
)


@contextmanager
def log_context(**fields: object) -> Iterator[None]:
    """Attach arbitrary key/value fields to log records emitted in this scope.

    Nested calls merge, but only shallowly. Inner values override outer values
    for the same key.

    No effect unless install_log_context_filter() has been called.
    """
    current = _log_context.get() or {}
    token = _log_context.set(current | fields)
    try:
        yield
    finally:
        _log_context.reset(token)


def install_log_context_filter() -> None:
    """Attach the logging context filter to root log handlers.

    Required in order to use log_context().

    Call once, after configure_logging().
    """
    filter_ = _LogContextFilter()
    for handler in logging.getLogger().handlers:
        handler.addFilter(filter_)


class _LogContextFilter(logging.Filter):
    @override
    def filter(self, record: logging.LogRecord) -> bool:
        ctx = _log_context.get()
        if ctx:
            suffix = " ".join(f"{k}={v}" for k, v in ctx.items())
            record.msg = f"{record.getMessage()} [{suffix}]"
            # Clear args since record.getMessage() has already applied them.
            record.args = None
        return True


class _TqdmStreamHandler(logging.StreamHandler[TextIO]):
    @override
    def emit(self, record: logging.LogRecord) -> None:
        tqdm.write(self.format(record), file=self.stream)
        self.flush()
