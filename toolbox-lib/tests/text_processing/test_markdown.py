import re
import textwrap

from toolbox.text_processing.markdown import TruncationResult, truncate_at_heading


class TestTruncationResult:
    def test_ratio_zero_when_nothing_truncated(self) -> None:
        result = TruncationResult(
            text="abc",
            original_length=3,
            truncated_length=3,
            matched_heading=None,
        )
        assert result.truncation_ratio == 0.0

    def test_ratio_half(self) -> None:
        result = TruncationResult(
            text="ab",
            original_length=4,
            truncated_length=2,
            matched_heading="## References",
        )
        assert result.truncation_ratio == 0.5


class TestTruncateAtHeading:
    def test_truncates_at_references_h2(self) -> None:
        markdown = textwrap.dedent("""
            # Paper Title

            ## Introduction

            Body text.

            ## References

            [1] Some citation.
        """).strip()
        result = truncate_at_heading(markdown)

        assert result.matched_heading == "## References"
        assert "Body text." in result.text
        assert "[1] Some citation." not in result.text
        assert result.original_length == len(markdown)
        assert 0 < result.truncated_length < result.original_length

    def test_picks_earliest_match_across_patterns(self) -> None:
        markdown = textwrap.dedent("""
            # Paper

            Body.

            ## Acknowledgments

            Thanks.

            ## References

            Citation.
        """).strip()
        result = truncate_at_heading(markdown)

        assert result.matched_heading == "## Acknowledgments"
        assert "Body." in result.text
        assert "Thanks." not in result.text
        assert "Citation." not in result.text

    def test_no_match_returns_unchanged(self) -> None:
        markdown = "# Paper\n\nJust body text, no tail sections."
        result = truncate_at_heading(markdown)

        assert result.text == markdown
        assert result.matched_heading is None
        assert result.original_length == len(markdown)
        assert result.truncated_length == len(markdown)
        assert result.truncation_ratio == 0.0

    def test_case_insensitive(self) -> None:
        markdown = "# Paper\n\nBody.\n\n## REFERENCES\n\nCitation."
        result = truncate_at_heading(markdown)
        assert result.matched_heading == "## REFERENCES"

    def test_word_boundary_avoids_false_match(self) -> None:
        markdown = "# Paper\n\n## User Preferences\n\nContent."
        result = truncate_at_heading(markdown)
        assert result.matched_heading is None

    def test_matches_heading_with_bold_markers(self) -> None:
        markdown = "# Paper\n\nBody.\n\n## **References**\n\nCitation."
        result = truncate_at_heading(markdown)
        assert result.matched_heading == "## **References**"

    def test_matches_numbered_heading(self) -> None:
        markdown = "# Paper\n\nBody.\n\n## 5. References and Notes\n\nCitation."
        result = truncate_at_heading(markdown)
        assert result.matched_heading == "## 5. References and Notes"

    def test_skips_h3_with_default_patterns(self) -> None:
        markdown = "# Paper\n\nBody.\n\n### References\n\nLooks like a tail but is H3."
        result = truncate_at_heading(markdown)
        assert result.matched_heading is None

    def test_custom_pattern(self) -> None:
        markdown = "# Paper\n\nBody.\n\n## Data Availability\n\nDataset URL."
        custom = (
            re.compile(
                r"^#{1,2}\s+.*\bdata availability\b.*$",
                re.MULTILINE | re.IGNORECASE,
            ),
        )
        result = truncate_at_heading(markdown, heading_patterns=custom)
        assert result.matched_heading == "## Data Availability"
        assert "Dataset URL." not in result.text

    def test_empty_markdown(self) -> None:
        result = truncate_at_heading("")
        assert result.text == ""
        assert result.matched_heading is None
        assert result.truncation_ratio == 0.0
