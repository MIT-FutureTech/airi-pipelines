from agora_screening.documents import cid_artefact_ratio, clip

_HEAD_FRACTION = 0.75


def test_short_text_is_not_truncated() -> None:
    result = clip("  a short document  ", max_chars=100, head_fraction=_HEAD_FRACTION)
    assert result.text == "a short document"
    assert not result.truncated
    assert result.original_length == len("a short document")


def test_long_text_keeps_head_and_tail() -> None:
    text = "HEAD" + ("x" * 1000) + "TAIL"
    result = clip(text, max_chars=100, head_fraction=_HEAD_FRACTION)
    assert result.truncated
    assert result.text.startswith("HEAD")
    assert result.text.endswith("TAIL")
    assert result.original_length == len(text)


def test_truncation_marker_states_how_much_was_dropped() -> None:
    text = "y" * 1000
    result = clip(text, max_chars=100, head_fraction=_HEAD_FRACTION)
    assert "900 characters omitted" in result.text


def test_truncated_length_is_the_budget_plus_the_marker() -> None:
    text = "z" * 5000
    max_chars = 400
    result = clip(text, max_chars=max_chars, head_fraction=_HEAD_FRACTION)
    assert result.text.count("z") == max_chars


def test_cid_artefact_ratio_is_zero_for_clean_text() -> None:
    assert cid_artefact_ratio("A perfectly ordinary sentence.") == 0.0


def test_cid_artefact_ratio_detects_glyph_codes() -> None:
    text = "(cid:3)(cid:36)(cid:37)"
    assert cid_artefact_ratio(text) == 1.0


def test_cid_artefact_ratio_of_empty_text() -> None:
    assert cid_artefact_ratio("") == 0.0
