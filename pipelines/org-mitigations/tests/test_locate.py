from org_mitigations.locate import Span, locate_quote

TEXT = "Intro.  Our board\noversees AI-\nbased tools.  Outro."


class TestLocateQuote:
    def test_finds_an_exact_quote(self) -> None:
        span = locate_quote("Intro.", TEXT)

        assert span == Span(start=0, end=6)

    def test_ignores_differences_in_whitespace(self) -> None:
        span = locate_quote("Our board oversees AI-based tools.", TEXT)

        assert span is not None
        assert TEXT[span.start : span.end] == "Our board\noversees AI-\nbased tools."

    def test_returns_none_for_a_quote_not_in_the_text(self) -> None:
        assert locate_quote("Our board oversees all tools.", TEXT) is None

    def test_returns_none_for_an_empty_quote(self) -> None:
        assert locate_quote("  \n", TEXT) is None
