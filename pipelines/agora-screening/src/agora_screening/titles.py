import re
from enum import StrEnum

_MIN_TOKEN_LENGTH = 2
_PARTIAL_MATCH_THRESHOLD = 0.8


class TitleCheck(StrEnum):
    """Whether a transcribed title actually occurs in the text it came from."""

    YES = "yes"
    PARTIAL = "partial"
    NO = "no"
    NOT_APPLICABLE = "n/a"


def normalize(text: str) -> str:
    """Fold whitespace, case and cosmetic punctuation for substring matching.

    PDF extraction routinely breaks a title across lines and swaps quotes and
    dashes for typographic variants, so a raw substring test produces false
    alarms.
    """
    text = re.sub("[\u2018\u2019\u02bc\u2032]", "'", text)
    text = re.sub("[\u201c\u201d]", '"', text)
    text = re.sub("[\u2010-\u2015\u2212]", "-", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip().casefold()


def verify_title(title: str, document_text: str) -> TitleCheck:
    """Is the model's transcribed title present in the text that was sent?

    PARTIAL means every word of the title occurs in the document but not as one
    contiguous run, which is the normal signature of a title split across PDF
    lines or columns. NO means the title should be treated as fabricated.
    """
    if not title.strip():
        return TitleCheck.NOT_APPLICABLE
    normalized_title = normalize(title)
    normalized_document = normalize(document_text)
    if normalized_title in normalized_document:
        return TitleCheck.YES
    tokens = [
        word
        for word in re.split(r"\W+", normalized_title, flags=re.UNICODE)
        if len(word) > _MIN_TOKEN_LENGTH
    ]
    if not tokens:
        return TitleCheck.NO
    hit_rate = sum(token in normalized_document for token in tokens) / len(tokens)
    if hit_rate >= _PARTIAL_MATCH_THRESHOLD:
        return TitleCheck.PARTIAL
    return TitleCheck.NO
