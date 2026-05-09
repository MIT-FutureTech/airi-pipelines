import logging
from enum import StrEnum

from pydantic import BaseModel, Field

from toolbox.llm import LLMClient, Message

logger = logging.getLogger(__name__)


class Decision(StrEnum):
    INCLUDE = "include"
    EXCLUDE = "exclude"
    UNCERTAIN = "uncertain"


class ScreeningResult(BaseModel):
    criteria_breakdown: str = Field(
        description=(
            "Full list of all criteria and whether the document meets each one."
            + " Write this before you make your decision."
        ),
    )
    decision: Decision = Field(
        description=(
            "Your final decision. Write this after assessing the document"
            + " against all the criteria."
        ),
    )


async def screen_abstract(client: LLMClient, abstract: str) -> ScreeningResult:
    return await _screen(
        client,
        system_prompt=ABSTRACT_SCREENING_SYSTEM_PROMPT,
        document=abstract,
    )


async def screen_full_text(client: LLMClient, full_text: str) -> ScreeningResult:
    return await _screen(
        client,
        system_prompt=FULL_TEXT_SCREENING_SYSTEM_PROMPT,
        document=full_text,
    )


async def _screen(
    client: LLMClient,
    *,
    system_prompt: str,
    document: str,
) -> ScreeningResult:
    messages = [
        Message(role="system", content=system_prompt),
        Message(role="user", content=_format_screening_user_prompt(document)),
    ]
    result = await client.generate_structured(messages, ScreeningResult)
    if result.usage is None:
        logger.info("No LLM usage returned")
    else:
        logger.info(f"Usage: {result.usage.model_dump_json()}")
    return result.value


_SCREENING_CRITERIA = """
## Inclusion criteria

Include a document if it:
I1. Is a review, article, or report (peer-reviewed or gray literature)
I2. Presents a novel framework, taxonomy, or other structured classification for AI risks
I3. Enumerates a list of concrete AI risks and applies the framework/taxonomy to them
I4. Addresses AI risks broadly, across multiple locations and industry sectors

## Exclusion criteria

Exclude a document if it:
E1. Is a book chapter, thesis, commentary, editorial, or protocol
E2. Focuses only on a single location, sector, or individual AI system (e.g. risks from DALL-E only, AI in radiology only)
E3. Focused only on a single risk category (e.g. solely about fairness, solely about deepfakes)
E4. Merely cites or discusses existing taxonomies/frameworks without proposing a new one
E5. Discusses AI impacts, outcomes, or consequences without specifying or classifying concrete risks
E6. Discusses sources of risk at a high level of abstraction (e.g. sociotechnical sources of risk in AI)
E7. Focuses on risk-assessment processes (e.g. how organizations can assess risks from AI) rather than classifying risks
E8. Is not in English

Interpret all the inclusion and exclusion criteria strictly. Have a high bar for
including a document.

## Decision

Respond with one of
- "include": the document clearly meets the all of the inclusion criteria and none of the exclusion criteria
- "exclude": the document clearly fails one or more inclusion criteria or meets one or more exclusion criteria
- "uncertain": you cannot confidently decide from the available text
"""

ABSTRACT_SCREENING_SYSTEM_PROMPT = f"""
You are a research screener for the AI Risk Repository, a living database of AI risks
classified according to multiple taxonomies. Your task is to decide whether a document
should be included for full-text review based on its title and abstract.

{_SCREENING_CRITERIA}
"""

FULL_TEXT_SCREENING_SYSTEM_PROMPT = f"""
You are a research screener for the AI Risk Repository, a living database of AI risks
classified according to multiple taxonomies. Your task is to decide whether a document
should be included in the repository.

{_SCREENING_CRITERIA}
"""

_SCREENING_USER_PROMPT = """
Decide whether the following document should be included.

<document>

{document}

</document>

In your response, first list all the criteria one-by-one and identify whether or
not the document meets each one. Then give your decision.
"""


def _format_screening_user_prompt(document: str) -> str:
    return _SCREENING_USER_PROMPT.format(document=document)
