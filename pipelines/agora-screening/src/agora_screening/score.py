import logging
from enum import StrEnum

from pydantic import BaseModel, Field

from agora_screening.corpus import DocumentRecord
from agora_screening.documents import ClippedText, cid_artefact_ratio, clip
from agora_screening.prompts import build_user_prompt
from agora_screening.results import PipelineStage, result_path, save
from agora_screening.settings import AgoraScreeningSettings
from agora_screening.titles import TitleCheck, verify_title
from toolbox.concurrency import ConcurrentMap
from toolbox.llm import LLMClient, Message, ToolboxLLMInvalidResponseError
from toolbox.log import log_context

logger = logging.getLogger(__name__)


class ScopeAssessment(BaseModel):
    """The model's structured judgement about one document."""

    name_original_language: str = Field(
        description=(
            "The document's own title, COPIED CHARACTER-FOR-CHARACTER from the supplied"
            " document text. This is a TRANSCRIPTION task, not a knowledge task. The"
            " string you return MUST literally appear in the document text supplied to"
            " you. NEVER reconstruct, recall, guess, translate back, or supply a title"
            " from your own prior knowledge of this document. If the document prints its"
            " title in a non-Latin script, copy that script exactly. If the supplied text"
            " is an official translation, or is simply an English-language document, its"
            " title IS English - return that English title and set the code to 'en'. If no"
            " title is discernible, return an empty string."
        ),
    )
    name_original_language_code: str = Field(
        description=(
            "ISO 639-1 two-letter code for the language of name_original_language. Use"
            " 'en' only if the document's own official title is genuinely English. Return"
            " an empty string if name_original_language is empty."
        ),
    )
    name_english: str = Field(
        description=(
            "The document's title in English. If the original title is already English,"
            " repeat it verbatim. If it is in another language, supply a faithful English"
            " translation - prefer the document's own official English rendering if it"
            " prints one. If no title appears in the text, fall back to the supplied"
            " initiative name."
        ),
    )
    scope_score: int = Field(
        ge=0,
        le=100,
        description=(
            "How well the document falls within AGORA's scope, 0-100, per the banded"
            " rubric in Section 4 of the scoping definition. 0 = definitively out of"
            " scope, 100 = unambiguously in scope."
        ),
    )
    scope_score_rationale: str = Field(
        description=(
            "2-4 sentences justifying the score. Must cite the specific AGORA criteria"
            " that drove it - notably whether the text is operative or non-operative,"
            " whether AI is addressed directly and substantively, and the proportion of"
            " the document AI occupies. Note explicitly if the supplied text was truncated"
            " or of poor extraction quality."
        ),
    )


class ScoreStatus(StrEnum):
    SUCCESS = "success"
    UNPARSEABLE_MODEL_OUTPUT = "failed: unparseable model output"


class ScoreResult(BaseModel):
    """One document's assessment plus everything needed to audit it.

    Failures are persisted rather than skipped, so the set of result files is a
    complete record of what was attempted.
    """

    readable_id: str
    slug: str
    status: ScoreStatus
    assessment: ScopeAssessment | None
    title_check: TitleCheck | None
    model: str | None
    input_tokens: int | None
    output_tokens: int | None
    chars_sent: int
    original_chars: int
    truncated: bool
    cid_artefact_ratio: float


async def _score_one(
    record: DocumentRecord,
    *,
    llm: LLMClient,
    system_prompt: str,
    settings: AgoraScreeningSettings,
) -> None:
    with log_context(readable_id=record.readable_id):
        output_path = result_path(
            settings.output_dir, PipelineStage.SCORE, record.readable_id
        )
        if not settings.force and output_path.exists():
            return
        document = clip(record.text, settings.max_chars, settings.head_fraction)
        user_prompt = build_user_prompt(record, document)
        messages = [
            Message(role="system", content=system_prompt),
            Message(role="user", content=user_prompt),
        ]
        try:
            result = await llm.generate_structured(messages, ScopeAssessment)
        except ToolboxLLMInvalidResponseError as error:
            logger.warning(f"Could not score document: {error!r}")
            save(output_path, _failure(record, document))
            return
        assessment = result.value
        save(
            output_path,
            ScoreResult(
                readable_id=record.readable_id,
                slug=record.slug,
                status=ScoreStatus.SUCCESS,
                assessment=assessment,
                title_check=verify_title(
                    assessment.name_original_language, document.text
                ),
                model=result.model,
                input_tokens=result.usage.input_tokens if result.usage else None,
                output_tokens=result.usage.output_tokens if result.usage else None,
                chars_sent=document.length,
                original_chars=document.original_length,
                truncated=document.truncated,
                cid_artefact_ratio=cid_artefact_ratio(document.text),
            ),
        )
        logger.info(f"Scope score: {assessment.scope_score}")


def _failure(record: DocumentRecord, document: ClippedText) -> ScoreResult:
    return ScoreResult(
        readable_id=record.readable_id,
        slug=record.slug,
        status=ScoreStatus.UNPARSEABLE_MODEL_OUTPUT,
        assessment=None,
        title_check=None,
        model=None,
        input_tokens=None,
        output_tokens=None,
        chars_sent=document.length,
        original_chars=document.original_length,
        truncated=document.truncated,
        cid_artefact_ratio=cid_artefact_ratio(document.text),
    )


async def run_scoring(
    records: list[DocumentRecord],
    *,
    llm: LLMClient,
    system_prompt: str,
    settings: AgoraScreeningSettings,
) -> None:
    runner = ConcurrentMap(
        max_concurrency=settings.concurrency,
        progress_description="Scoring documents",
    )
    async for _ in runner.map(
        records,
        _score_one,
        llm=llm,
        system_prompt=system_prompt,
        settings=settings,
    ):
        pass
