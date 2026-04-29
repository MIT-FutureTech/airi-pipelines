import logging
import re
from collections.abc import Iterable

from pydantic import BaseModel

logger = logging.getLogger(__name__)


_TAIL_HEADING_KEYWORDS = (
    "references",
    "bibliography",
    "works cited",
    "appendix",
    "appendices",
    "supplementary",
    "supplemental",
    "acknowledgments",
    "acknowledgements",
)


DEFAULT_TAIL_HEADING_PATTERNS: tuple[re.Pattern[str], ...] = tuple(
    re.compile(rf"^#{{1,2}}\s+.*\b{kw}\b.*$", re.MULTILINE | re.IGNORECASE)
    for kw in _TAIL_HEADING_KEYWORDS
)


class TruncationResult(BaseModel):
    text: str
    original_length: int
    truncated_length: int
    matched_heading: str | None

    @property
    def truncation_ratio(self) -> float:
        if self.original_length == 0:
            return 0.0
        return 1.0 - self.truncated_length / self.original_length


def truncate_at_heading(
    markdown: str,
    heading_patterns: Iterable[re.Pattern[str]] = DEFAULT_TAIL_HEADING_PATTERNS,
) -> TruncationResult:
    earliest_match: re.Match[str] | None = None
    for pattern in heading_patterns:
        match = pattern.search(markdown)
        if match is None:
            continue
        if earliest_match is None or match.start() < earliest_match.start():
            earliest_match = match

    if earliest_match is None:
        logger.info("No tail heading matched; returning original markdown unchanged")
        return TruncationResult(
            text=markdown,
            original_length=len(markdown),
            truncated_length=len(markdown),
            matched_heading=None,
        )

    truncated_text = markdown[: earliest_match.start()]
    result = TruncationResult(
        text=truncated_text,
        original_length=len(markdown),
        truncated_length=len(truncated_text),
        matched_heading=earliest_match.group(0).strip(),
    )
    logger.info(
        f"Truncated at heading {result.matched_heading!r}:"
        + f" {result.original_length:,d} -> {result.truncated_length:,d} chars"
        + f" ({result.truncation_ratio:.1%} removed)"
    )
    return result
