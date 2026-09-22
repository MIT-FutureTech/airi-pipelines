import re

from pydantic import BaseModel

CID_ARTEFACT_PATTERN = re.compile(r"\(cid:\d+\)")


class ClippedText(BaseModel, frozen=True):
    """Document text trimmed to fit the prompt, with what that cost recorded."""

    text: str
    truncated: bool
    original_length: int

    @property
    def length(self) -> int:
        return len(self.text)


def clip(text: str, max_chars: int, head_fraction: float) -> ClippedText:
    """Trim to max_chars, keeping the head and a sample of the tail.

    Scope clauses live at the head; annexes, schedules and signature blocks live
    at the tail. The middle is the most expendable part of a long instrument.
    """
    text = text.strip()
    if len(text) <= max_chars:
        return ClippedText(text=text, truncated=False, original_length=len(text))
    head_chars = int(max_chars * head_fraction)
    tail_chars = max_chars - head_chars
    omitted = len(text) - max_chars
    marker = (
        f"\n\n[... {omitted:,} characters omitted from the middle of this document"
        f" ({len(text):,} characters total). The excerpt below resumes at the end"
        " of the document. ...]\n\n"
    )
    return ClippedText(
        text=text[:head_chars] + marker + text[-tail_chars:],
        truncated=True,
        original_length=len(text),
    )


def cid_artefact_ratio(text: str) -> float:
    """Fraction of a document's characters taken up by `(cid:NNN)` glyph codes.

    A PDF whose font encoding could not be resolved extracts as these codes
    rather than letters. Two documents in the OECD corpus are more than half
    artefact and were still scored 75 by the proof of concept, so this is
    measured rather than left for the model to notice.
    """
    if not text:
        return 0.0
    artefact_chars = sum(
        len(match.group()) for match in CID_ARTEFACT_PATTERN.finditer(text)
    )
    return artefact_chars / len(text)
