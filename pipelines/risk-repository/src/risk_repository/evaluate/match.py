import logging
from pathlib import Path

from pydantic import BaseModel, Field

from risk_repository.evaluate.ground_truth import GroundTruth, GroundTruthRisk
from risk_repository.extract import ExtractedRisk, ExtractionResult
from risk_repository.results import PipelineStage, load, result_path
from toolbox.concurrency import ConcurrentMap
from toolbox.llm import LLMClient, Message

logger = logging.getLogger(__name__)


class MatchPair(BaseModel):
    gt_index: int
    pipeline_index: int


class DocumentMatchResult(BaseModel):
    readable_id: str
    gt_risks: list[GroundTruthRisk]
    pipeline_risks: list[ExtractedRisk]
    matches: list[MatchPair]


class _LLMMatchPair(BaseModel):
    reasoning: str = Field(
        description="Brief explanation of why these two risks match."
    )
    gt_id: str = Field(description='ID of the ground truth risk (e.g. "gt-002").')
    pipeline_id: str = Field(description='ID of the pipeline risk (e.g. "pl-002").')


class _LLMMatchResponse(BaseModel):
    matches: list[_LLMMatchPair]


class _MatchValidationError(Exception):
    valid_matches: list[_LLMMatchPair]

    def __init__(self, errors: list[str], valid_matches: list[_LLMMatchPair]) -> None:
        self.valid_matches = valid_matches
        super().__init__("\n".join(errors))


class _MatchInput(BaseModel):
    readable_id: str
    gt_risks: list[GroundTruthRisk]
    pipeline_risks: list[ExtractedRisk]


async def _match_one(
    inp: _MatchInput,
    *,
    llm: LLMClient,
    max_attempts: int,
) -> DocumentMatchResult:
    if inp.gt_risks and inp.pipeline_risks:
        llm_matches = await _match_risks(
            llm, inp.gt_risks, inp.pipeline_risks, max_attempts=max_attempts
        )
        matches = [_to_match_pair(m) for m in llm_matches]
        logger.info(
            f"{inp.readable_id}: {len(matches)} matches (GT={len(inp.gt_risks)}, pipeline={len(inp.pipeline_risks)})"
        )
    else:
        matches = []
    return DocumentMatchResult(
        readable_id=inp.readable_id,
        gt_risks=inp.gt_risks,
        pipeline_risks=inp.pipeline_risks,
        matches=matches,
    )


async def match_all(
    ground_truth: GroundTruth,
    results_dir: Path,
    llm: LLMClient,
    *,
    concurrency: int,
    max_attempts: int,
) -> list[DocumentMatchResult]:
    gt_by_doc = ground_truth.risks_by_document()

    inputs: list[_MatchInput] = []
    for doc in ground_truth.documents:
        extraction_path = result_path(
            output_dir=results_dir,
            stage=PipelineStage.EXTRACT,
            readable_id=doc.readable_id,
        )
        if not extraction_path.exists():
            continue
        extraction = load(extraction_path, ExtractionResult)
        inputs.append(
            _MatchInput(
                readable_id=doc.readable_id,
                gt_risks=gt_by_doc.get(doc.readable_id, []),
                pipeline_risks=extraction.risks,
            )
        )

    runner = ConcurrentMap(max_concurrency=concurrency, progress_description="Matching")
    results: list[DocumentMatchResult] = []
    async for result in runner.map(
        inputs,
        _match_one,
        llm=llm,
        max_attempts=max_attempts,
    ):
        results.append(result)
    return results


def _to_match_pair(llm_match: _LLMMatchPair) -> MatchPair:
    return MatchPair(
        gt_index=int(llm_match.gt_id.removeprefix("gt-")),
        pipeline_index=int(llm_match.pipeline_id.removeprefix("pl-")),
    )


async def _match_risks(
    llm: LLMClient,
    gt_risks: list[GroundTruthRisk],
    pipeline_risks: list[ExtractedRisk],
    *,
    max_attempts: int,
) -> list[_LLMMatchPair]:
    messages: list[Message] = [
        Message(role="system", content=_MATCHING_SYSTEM_PROMPT),
        Message(role="user", content=_format_user_message(gt_risks, pipeline_risks)),
    ]
    for attempt in range(max_attempts):
        result = await llm.generate_structured(messages, _LLMMatchResponse)
        try:
            return _validate_matches(
                result.value.matches,
                gt_count=len(gt_risks),
                pipeline_count=len(pipeline_risks),
            )
        except _MatchValidationError as exc:
            logger.warning(f"Match validation failed (attempt {attempt + 1}): {exc}")
            if attempt + 1 == max_attempts:
                return exc.valid_matches
            messages.append(
                Message(role="assistant", content=result.value.model_dump_json())
            )
            messages.append(
                Message(
                    role="user",
                    content=f"Your response had errors:\n{exc}\n\nPlease fix these errors and try again.",
                )
            )
    raise AssertionError("unreachable")


def _validate_matches(
    matches: list[_LLMMatchPair],
    *,
    gt_count: int,
    pipeline_count: int,
) -> list[_LLMMatchPair]:
    gt_ids = {_gt_id(i) for i in range(gt_count)}
    pipeline_ids = {_pipeline_id(i) for i in range(pipeline_count)}
    valid: list[_LLMMatchPair] = []
    errors: list[str] = []
    used_gt: set[str] = set()
    used_pipeline: set[str] = set()
    for match in matches:
        if match.gt_id not in gt_ids:
            errors.append(f"Unknown ground truth ID {match.gt_id!r}")
            continue
        if match.pipeline_id not in pipeline_ids:
            errors.append(f"Unknown pipeline ID {match.pipeline_id!r}")
            continue
        if match.gt_id in used_gt or match.pipeline_id in used_pipeline:
            errors.append(
                f"Duplicate: {match.gt_id!r} or {match.pipeline_id!r} already matched"
            )
            continue
        used_gt.add(match.gt_id)
        used_pipeline.add(match.pipeline_id)
        valid.append(match)
    if errors:
        raise _MatchValidationError(errors, valid)
    return valid


def _gt_id(index: int) -> str:
    return f"gt-{index:03}"


def _pipeline_id(index: int) -> str:
    return f"pl-{index:03}"


def _format_gt_risk(index: int, risk: GroundTruthRisk) -> str:
    return _GT_RISK_TEMPLATE.format(
        id=_gt_id(index),
        category=risk.category,
        subcategory=risk.subcategory,
        description=risk.description,
    )


def _format_pipeline_risk(index: int, risk: ExtractedRisk) -> str:
    return _PIPELINE_RISK_TEMPLATE.format(
        id=_pipeline_id(index),
        category=risk.category,
        subcategory=risk.subcategory,
        quote=risk.supporting_quote,
        description=risk.description,
    )


def _format_user_message(
    gt_risks: list[GroundTruthRisk],
    pipeline_risks: list[ExtractedRisk],
) -> str:
    gt_formatted = "\n\n".join(_format_gt_risk(i, r) for i, r in enumerate(gt_risks))
    pipeline_formatted = "\n\n".join(
        _format_pipeline_risk(i, r) for i, r in enumerate(pipeline_risks)
    )
    return _MATCHING_USER_PROMPT.format(
        gt_risks=gt_formatted, pipeline_risks=pipeline_formatted
    )


_MATCHING_SYSTEM_PROMPT = """
You are comparing risks extracted by an automated pipeline against human-coded
ground truth risks from the same academic paper. Your task is to find one-to-one
matches.

## Matching criteria

A match means the pipeline risk and ground truth risk refer to the SAME specific risk:
- The category and subcategory should be nearly identical (same wording or trivial rewording).
- The pipeline's supporting quote should closely correspond to the ground truth description.
- The pipeline's description may be paraphrased but must refer to the same specific risk.
- Do NOT match risks that merely fall under the same general topic or domain.

## Rules

- Each ground truth risk can match at most one pipeline risk, and vice versa.
- Not every risk needs a match. Only match risks you are confident refer to the same thing.
- Return an empty list if no matches exist.
"""

_MATCHING_USER_PROMPT = """
## Ground truth risks

{gt_risks}

## Pipeline-extracted risks

{pipeline_risks}

Produce one-to-one matches between these two lists.
"""

_GT_RISK_TEMPLATE = """
<ground-truth-risk id="{id}">
Category: {category}
Subcategory: {subcategory}
Description: {description}
</ground-truth-risk>
"""

_PIPELINE_RISK_TEMPLATE = """
<pipeline-risk id="{id}">
Category: {category}
Subcategory: {subcategory}
Quote: {quote}
Description: {description}
</pipeline-risk>
"""
