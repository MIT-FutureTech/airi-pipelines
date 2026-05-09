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
    reasoning: str = Field(
        description="One sentence explaining your decision. Generate this before your decision."
    )
    decision: Decision


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

Include documents that:
- Are reviews, articles, or reports (peer-reviewed or gray literature)
- Enumerate concrete risks from AI using novel frameworks, taxonomies, or other structured classifications
- Address AI risks broadly, across multiple locations and industry sectors

## Exclusion criteria

Exclude documents that:
- Are book chapters, theses, commentaries, editorials, or protocols
- Focus only on a single location, sector, or specific AI tool (e.g. risks from DALL-E only, AI in radiology only)
- Focus only on a single risk category (e.g. solely about fairness, solely about deepfakes)
- Merely cite or discuss existing taxonomies/frameworks without proposing a new one
- Discuss AI impacts, outcomes, or consequences without specifying or classifying concrete risks
- Discuss sources of risk at a high level of abstraction (e.g. sociotechnical sources of risk in AI)
- Focus on risk-assessment processes (e.g. how organizations can assess risks from AI) rather than classifying risks
- Are not in English

## Decision

Respond with one of
- "include": the document clearly meets the inclusion criteria
- "exclude": the document clearly meets one or more exclusion criteria
- "uncertain": you cannot confidently decide from the available text

Provide your reasoning and then your decision.
"""

ABSTRACT_SCREENING_SYSTEM_PROMPT = f"""
You are a research screener for the AI Risk Repository, a living database of AI risk
classifications. Your task is to decide whether a document should be included for
full-text review based on its title and abstract.

{_SCREENING_CRITERIA}
"""

FULL_TEXT_SCREENING_SYSTEM_PROMPT = f"""
You are a research screener for the AI Risk Repository, a living database of AI risk
classifications. Your task is to decide whether a document should be included in the
repository.

{_SCREENING_CRITERIA}
"""

_SCREENING_USER_PROMPT = """
Decide whether the following document should be included.

<document>

{document}

</document>
"""


def _format_screening_user_prompt(document: str) -> str:
    return _SCREENING_USER_PROMPT.format(document=document)
