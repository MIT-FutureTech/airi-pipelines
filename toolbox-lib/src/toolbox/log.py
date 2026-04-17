import logging
from collections.abc import Iterable
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


class _TqdmStreamHandler(logging.StreamHandler[TextIO]):
    @override
    def emit(self, record: logging.LogRecord) -> None:
        tqdm.write(self.format(record), file=self.stream)
        self.flush()
