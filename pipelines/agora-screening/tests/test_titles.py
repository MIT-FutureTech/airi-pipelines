from agora_screening.titles import TitleCheck, normalize, verify_title

CURLY_APOSTROPHE = chr(0x2019)
LEFT_DOUBLE_QUOTE = chr(0x201C)
RIGHT_DOUBLE_QUOTE = chr(0x201D)
EN_DASH = chr(0x2013)
EM_DASH = chr(0x2014)


def test_normalize_folds_case_and_whitespace() -> None:
    assert normalize("  National   AI\nStrategy ") == "national ai strategy"


def test_normalize_folds_typographic_punctuation() -> None:
    curly = (
        f"Egypt{CURLY_APOSTROPHE}s {LEFT_DOUBLE_QUOTE}AI{RIGHT_DOUBLE_QUOTE}"
        f" Charter {EN_DASH} Phase 2"
    )
    straight = 'Egypt\'s "AI" Charter - Phase 2'
    assert normalize(curly) == normalize(straight)


def test_verify_title_finds_exact_match() -> None:
    document = "Ministry of Digital Affairs\n\nNational AI Strategy\n\n1. Purpose"
    assert verify_title("National AI Strategy", document) == TitleCheck.YES


def test_verify_title_matches_across_typographic_variants() -> None:
    document = f"Preamble\nEgypt{CURLY_APOSTROPHE}s AI Charter {EM_DASH} Second Edition"
    assert (
        verify_title("Egypt's AI Charter - Second Edition", document) == TitleCheck.YES
    )


def test_verify_title_matches_a_title_broken_across_lines() -> None:
    document = "NATIONAL\nARTIFICIAL INTELLIGENCE\nSTRATEGY\nof the Republic"
    assert (
        verify_title("National Artificial Intelligence Strategy", document)
        == TitleCheck.YES
    )


def test_verify_title_reports_partial_when_words_are_not_contiguous() -> None:
    document = (
        "National Strategy for the Republic\n\nOn Artificial Intelligence\n\nArticle 1"
    )
    assert (
        verify_title("National Artificial Intelligence Strategy", document)
        == TitleCheck.PARTIAL
    )


def test_verify_title_rejects_a_fabricated_title() -> None:
    """The Egypt failure: a title the model supplied from prior knowledge.

    Gemini returned a native-script title for a document that contained no such
    script at all, and a different one on each run. The script does not matter
    to the check; absence from the supplied text does.
    """
    document = (
        "Guide to Egypt's National AI Governance Framework. This document sets out."
    )
    assert (
        verify_title("Estrategia Nacional de Inteligencia Artificial", document)
        == TitleCheck.NO
    )


def test_verify_title_reports_not_applicable_for_empty_title() -> None:
    assert verify_title("   ", "any document text") == TitleCheck.NOT_APPLICABLE
