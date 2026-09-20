from pathlib import Path

from agora_screening.corpus import DocumentRecord
from agora_screening.documents import ClippedText

DEFAULT_RUBRIC_PATH = Path(__file__).parent.parent.parent / "prompts" / "agora_scope.md"

SYSTEM_PROMPT_TEMPLATE = """\
You are a screening analyst for AGORA, the CSET (Center for Security and Emerging
Technology) database of AI governance documents. Your job is to decide how well a
document falls within AGORA's scope and to score it 0-100.

The complete AGORA scoping definition, heuristics, and the 0-100 banded rubric you
must apply are given below. Apply them exactly, including the scoring reminders in
Section 4.

Judge the DOCUMENT TEXT supplied to you. The initiative metadata (name, jurisdiction,
category) is context supplied by the OECD aggregator, not evidence of scope - a
promising title does not make an out-of-scope document in scope.

=== BEGIN AGORA SCOPING DEFINITION ===
{rubric}
=== END AGORA SCOPING DEFINITION ===

TITLE EXTRACTION RULE. `name_original_language` is a TRANSCRIPTION field, not a
knowledge field. It is subject to one absolute constraint:

  *** The string you put in `name_original_language` MUST appear verbatim in the
document text supplied below. It is checked programmatically against that text. ***

  - Copy the title character-for-character as printed, in whatever script it is
printed in. If the document prints its title in Arabic, Hangul, Japanese, Hanzi,
Cyrillic, Hebrew or Thai, copy that script exactly.
  - NEVER reconstruct a native-language title from your own prior knowledge of the
document. If you recognise the document and know its official native title, that is
IRRELEVANT unless that exact title is printed in the supplied text. Inventing a
plausible native title is the single worst failure mode for this field.
  - A great many documents from non-anglophone jurisdictions are published in
English, or are supplied here as official translations. For those, the title in the
supplied text IS English. Return that English title and set the code to "en". This is
CORRECT behaviour, not a failure - do not manufacture a foreign-language title to
avoid it.
  - If the document is genuinely bilingual and prints both, return the native-script
title here and the English one in `name_english`.
  - `name_original_language_code` must be the ISO 639-1 code of whatever you actually
put in `name_original_language`.

Respond only with the structured object required by the schema."""

_USER_PROMPT_TEMPLATE = """\
## Initiative metadata (context only)
{metadata}
{truncation_note}
## Document text (the evidence - judge this)
```
{document}
```

Score this document 0-100 for how well it falls within AGORA's scope, and extract its
title in the original language and in English."""

_TRUNCATION_NOTE = """
NOTE: this document was too long to send in full and has been truncated. Score what is
present and say so in your rationale.
"""


def load_rubric(path: Path) -> str:
    """Read the scoping definition injected wholesale into the system prompt.

    Kept as a file rather than a Python string so it can be tuned by someone who
    does not write Python, which is the intended way to adjust scoring.
    """
    return path.read_text(encoding="utf-8")


def build_system_prompt(rubric: str) -> str:
    return SYSTEM_PROMPT_TEMPLATE.format(rubric=rubric)


def build_user_prompt(record: DocumentRecord, document: ClippedText) -> str:
    fields = [
        ("Initiative name (OECD-supplied, may be a translation)", record.name),
        ("Jurisdiction", record.jurisdiction),
        ("Organization", record.organization),
        ("Date introduced", record.date_introduced),
        ("OECD category", record.category),
        ("OECD initiative type", record.initiative_type),
        ("Binding status (OECD-supplied)", record.binding),
        ("OECD summary", record.summary),
    ]
    metadata = "\n".join(
        f"- {label}: {value}" for label, value in fields if value.strip()
    )
    return _USER_PROMPT_TEMPLATE.format(
        metadata=metadata,
        truncation_note=_TRUNCATION_NOTE if document.truncated else "",
        document=document.text,
    )
