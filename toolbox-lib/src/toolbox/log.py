import logging
from collections.abc import Iterable
from pathlib import Path


def configure_logging(
    level: int,
    *,
    filepath: Path | None = None,
    loggers_to_silence: Iterable[str] = (),
) -> None:
    """Configure log level, format and handlers.

    This must be called before any log messages are emitted.
    """
    handlers: list[logging.Handler] = [logging.StreamHandler()]
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
