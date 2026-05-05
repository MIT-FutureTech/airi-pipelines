from collections.abc import Container
from enum import StrEnum

from pydantic import BaseModel, Field

from toolbox.llm import LLMClient, Message


class Decision(StrEnum):
    INCLUDE = "include"
    EXCLUDE = "exclude"
    UNCERTAIN = "uncertain"


class ScreenStage(StrEnum):
    FIRST_PAGE = "first_page"
    FULL_TEXT = "full_text"


class _LLMScreeningResponse(BaseModel):
    reasoning: str = Field(
        description="One sentence explaining your decision. Generate this before your decision."
    )
    decision: Decision


class ScreenStageResult(_LLMScreeningResponse):
    screen_stage: ScreenStage


class ScreeningResult(BaseModel):
    screen_stages: list[ScreenStageResult]

    @property
    def decision(self) -> Decision:
        return self.screen_stages[-1].decision


async def screen_document(
    client: LLMClient,
    *,
    stages_to_run: Container[ScreenStage],
    first_page: str,
    full_text: str,
) -> ScreeningResult:
    stages: list[ScreenStageResult] = []
    if ScreenStage.FIRST_PAGE in stages_to_run:
        stage1 = await _screen(
            client,
            system_prompt=FIRST_PAGE_SCREENING_SYSTEM_PROMPT,
            document=first_page,
        )
        stages.append(
            ScreenStageResult(
                screen_stage=ScreenStage.FIRST_PAGE, **stage1.model_dump()
            )
        )
        if stage1.decision == Decision.EXCLUDE:
            return ScreeningResult(screen_stages=stages)
    if ScreenStage.FULL_TEXT in stages_to_run:
        stage2 = await _screen(
            client,
            system_prompt=FULL_TEXT_SCREENING_SYSTEM_PROMPT,
            document=full_text,
        )
        stages.append(
            ScreenStageResult(screen_stage=ScreenStage.FULL_TEXT, **stage2.model_dump())
        )
    return ScreeningResult(screen_stages=stages)


async def _screen(
    client: LLMClient,
    *,
    system_prompt: str,
    document: str,
) -> _LLMScreeningResponse:
    messages = [
        Message(role="system", content=system_prompt),
        Message(role="user", content=format_screening_user_prompt(document)),
    ]
    result = await client.generate_structured(messages, _LLMScreeningResponse)
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

FIRST_PAGE_SCREENING_SYSTEM_PROMPT = f"""
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


def format_screening_user_prompt(document: str) -> str:
    return _SCREENING_USER_PROMPT.format(document=document)
