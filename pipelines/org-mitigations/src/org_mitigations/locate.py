from pydantic import BaseModel


class Span(BaseModel):
    start: int
    end: int


def locate_quote(quote: str, text: str) -> Span | None:
    """Find a quote in some text, ignoring whitespace."""
    positions = [i for i, char in enumerate(text) if not char.isspace()]
    compact_text = "".join(text[i] for i in positions)
    compact_quote = "".join(char for char in quote if not char.isspace())
    if not compact_quote:
        return None
    start = compact_text.find(compact_quote)
    if start == -1:
        return None
    last = start + len(compact_quote) - 1
    return Span(start=positions[start], end=positions[last] + 1)
