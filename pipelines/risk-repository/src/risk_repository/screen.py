import logging
from enum import StrEnum
from pathlib import Path
from typing import Literal

import httpx
from pydantic import BaseModel, Field

from risk_repository.documents import format_abstract_and_title, get_full_text
from risk_repository.records import DocumentRecord
from risk_repository.results import (
    PipelineStage,
    invalidate_downstream,
    load,
    result_path,
    save,
)
from risk_repository.settings import RiskRepositorySettings
from toolbox.concurrency import ConcurrentMap
from toolbox.llm import LLMClient, Message
from toolbox.log import log_context

logger = logging.getLogger(__name__)


class Decision(StrEnum):
    INCLUDE = "include"
    EXCLUDE = "exclude"
    UNCERTAIN = "uncertain"


class AbstractScreeningResult(BaseModel):
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


class FullTextScreeningResult(BaseModel):
    criteria_breakdown: str = Field(
        description=(
            "Full list of all criteria and the degree to which the document meets each"
            + " one, accounting for ambiguities. Write this before you make your"
            + " prediction."
        ),
    )
    predicted_include_count: int = Field(
        description=(
            "Integer between 0 and 10 (inclusive) for the predicted number of screeners"
            + " who will choose to include this document. Write this after assessing"
            + " the document against all the criteria."
        ),
    )


_ABSTRACT_SCREENING_SYSTEM_PROMPT = """\
You are a research screener for the AI Risk Repository, a living database of AI risks
classified according to multiple taxonomies. Your task is to decide whether a document
should be included for full-text review based on its title and abstract.

## Screening criteria

### 1: Document Type

Acceptable: a review, article, or report (peer-reviewed or gray literature)
Not acceptable: a book chapter, thesis, commentary, editorial, protocol
Not acceptable: a review, article, or report not written in English

### 2: Risk Requirement

Acceptable: the document frames its content in terms of the possibility of an
unfortunate occurrence associated with the development or deployment of AI (Society for
Risk Analysis definition).

Not acceptable: the document discusses impacts, outcomes, transformations, or other
consequences of AI without specifying negative or unfortunate occurrences.

Green flags
- Terms such as harms, adverse impacts, dangers, threats, negative consequences, undesirable outcomes, challenges.

Yellow flags:
- Terms such as benefits, opportunities, transformations, capabilities
- Aspirational or principles framing: Abstract uses "should", "ought", "ethical AI", "responsible AI", "principles for", without identifying specific negative outcomes.
- The abstract mixes conceptual levels: some are clearly risks but others are governance considerations, principles, technical features, or stakeholder concerns. If the one has to do work to read the list as a risk taxonomy, it probably isn't one.

Red flags:
- "This paper examines the societal impacts of generative AI" without signalling negative outcomes
- A document framed in terms of capabilities or applications

It is usually not sufficient for a paper to discuss only principles (for responsible /
ethical / safe AI). For instance, "principles for ethical AI" are likely to include
things like "fair" and "transparent", but these are not risks.

### 3: Novel Taxonomy of AI Risks

Acceptable: a document which proposes, develops, or explains a novel framework,
taxonomy, typology, classification, ontology, or similarly structured scheme of risks
from AI. We want the framework as presented by the original authors to minimize
misinterpretation.

Not acceptable: a document that merely cites or discusses existing theories, frameworks,
models, taxonomies, or classifications rather than proposing and explaining them.

Not acceptable: a document discussing sources of sociotechnical risk in AI at a high
level of abstraction without proposing a structured classification of specific risks.

Not acceptable: a document framing risk sources as colonialism, capitalism, surveillance
societies, the political economy of AI, sociotechnical configurations, etc.
where the unit of analysis is the upstream cause rather than specific outcomes.

Not acceptable: a document which discusses AI risks and proposes a novel framework for
how to ways to address, mitigate or govern those risks, rather than classifying the
risks themselves.

Acceptable: a document that present a substantive risk taxonomy as part of an assessment
methodology.

Green flags:
- Multi-domain breadth: List of risks spanning visibly different domains (e.g. environmental harm, discrimination, autonomous weapons, dangerous capabilities). **This is the strongest single positive signal in the abstract.**
- Explicit taxonomic framing: "taxonomy", "typology", "classification", "framework", "categorisation", "ontology" occurring near discussion of specific risks.
- Explicit structural terms: "categories", "domains", "dimensions", "types" (of risk)

Yellow flags:
- "a framework for AI risk management"
- "audit methodology for AI systems"
- "how to conduct an AI impact assessment"
- "a new benchmark for measuring the safety of frontier AI models"

### 4: Cross-cutting

The risks identified are present across multiple locations and industry sectors, or the
framework is explicitly intended to apply cross-sectorally. A paper may use examples
from one sector if its framework is presented as general.

Acceptable: a framework with examples from healthcare and finance and employment.

Acceptable: a framework presented as cross-cutting that uses healthcare as the running
example.

Acceptable: a framework focused on a single broad risk domain (e.g. environmental harms
from AI, types of AI-driven discrimination) at the cross-cutting level.

Not acceptable: a framework explicitly scoped to a location or single sector (e.g.
"risks from AI in radiology", "employment discrimination") with no claim to broader
applicability.

Not acceptable: a document focused on risks from very specific AI tools or models.

Yellow flags:
- ChatGPT, Claude, DALL-E, MidJourney, Sora, Grok, other AI product names. However, generic categories of AI are OK, like "AI assistant" or "agentic coding assistant."

## Worked examples

The reasoning for each example is highly abbreviated, containing only the crucial
considerations. Please be more thorough in your reasoning.

> We present a taxonomy of risks from large language models, organised across four
> categories: discrimination and toxicity, information hazards, misinformation harms,
> and human-computer interaction harms.
Criteria: multi-category list, explicit taxonomic framing, cross-cutting
Decision: include

> We propose a taxonomy of environmental harms from AI, with five categories and
> twenty-five subcategories spanning training emissions, hardware lifecycle, deployment
> energy, induced consumption, and ecosystem impacts.
Criteria: single domain but adds granularity within a domain that is very broad
Decision: include

> AI is transforming the global economy. This paper examines the implications of AI
> adoption for labour markets, productivity, and innovation.
Criteria: impact-only framing, no specification of negative outcomes.
Decision: exclude

> We propose a framework for responsible AI in radiology, addressing fairness,
> transparency, accountability, and clinical validity.
Criteria: single sector, principles-based framing rather than risk classification
Decision: exclude

> This paper examines colonialism as a source of risk in artificial intelligence
> systems, arguing that the political economy of AI development reproduces colonial
> logics.
Criteria: sources of risk at high abstraction
Decision: exclude

> We present a literature review of AGI safety research, covering some of the technical
> risks that must be addressed for safe development of advanced AI.
Criteria: citing rather than proposing; risk discussion is incidental to the literature review framing
Decision: exclude

## Decision

In your response, reason through the four criteria one by one. Avoid anchoring on a
decision until you've reasoned through all of them.

Since you're only seeing a portion of the document, it may not be possible to
definitively evaluate it against all criteria.

For your final decision, choose from
- "include": the document clearly meets the all of the inclusion criteria and none of the exclusion criteria
- "exclude": the document clearly fails one or more inclusion criteria or meets one or more exclusion criteria
- "uncertain": you cannot confidently decide from the available text. The document does not appear to violate any inclusion criteria or meet any exclusion criteria.
"""

_ABSTRACT_SCREENING_USER_PROMPT = """
Decide whether the following document should be included.

<document>

{document}

</document>

In your response, reason through all the criteria one-by-one and identify whether or
not the document meets each one. Then give your decision.
"""

FULL_TEXT_SCREENING_SYSTEM_PROMPT = """
You are helping the AI Risk Repository, a living database of AI risks classified
according to multiple taxonomies. Your task is to predict whether a document will be
chosen for inclusion based on the given criteria.

10 undergraduate students will each be given the screening criteria and the document
below. They will each independently decide whether to include it. You must predict how
many of the screeners will choose to include it. Keep in mind that different screeners
will interpret the instructions and the paper slightly differently. Account for this in
your prediction. This process will be repeated across many documents. You will be
evaluated on the accuracy of your predictions over all documents using a proper scoring
rule.

## Screening criteria (also provided to screeners)

### 1: Document Type

Acceptable: a review, article, or report (peer-reviewed or gray literature)
Not acceptable: a book chapter, thesis, commentary, editorial, protocol
Not acceptable: a review, article, or report not written in English

### 2: Risk Requirement

Acceptable: the document frames its content in terms of the possibility of an
unfortunate occurrence associated with the development or deployment of AI (Society for
Risk Analysis definition).

Not acceptable: the document discusses impacts, outcomes, transformations, or other
consequences of AI without specifying negative or unfortunate occurrences.

Green flags
- Terms such as harms, adverse impacts, dangers, threats, negative consequences, undesirable outcomes, challenges.

Yellow flags:
- Terms such as benefits, opportunities, transformations, capabilities
- Aspirational or principles framing: Abstract uses "should", "ought", "ethical AI", "responsible AI", "principles for", without identifying specific negative outcomes.
- The abstract mixes conceptual levels: some are clearly risks but others are governance considerations, principles, technical features, or stakeholder concerns. If the one has to do work to read the list as a risk taxonomy, it probably isn't one.

Red flags:
- "This paper examines the societal impacts of generative AI" without signalling negative outcomes
- A document framed in terms of capabilities or applications

It is usually not sufficient for a paper to discuss only principles (for responsible /
ethical / safe AI). For instance, "principles for ethical AI" are likely to include
things like "fair" and "transparent", but these are not risks.

### 3: Taxonomy of AI Risks

Acceptable: a document that proposes a framework, taxonomy, typology, classification,
ontology, or similarly structured scheme of risks from AI, presented as a large table.

Not acceptable: a document which uses terms like "framework" in its abstract or
conclusion but does not contain a list or table laying out the risks in a systematic way.

Not acceptable: a document which mentions risks as motivating examples in its
introduction or conclusion but does not enumerate them in a structured list, table or
diagram.

Not acceptable: a document discussing sources of sociotechnical risk in AI at a high
level of abstraction without proposing a structured classification of specific risks.

Not acceptable: a document framing risk sources as colonialism, capitalism, surveillance
societies, the political economy of AI, sociotechnical configurations, etc.
where the unit of analysis is the upstream cause rather than specific outcomes.

Not acceptable: a taxonomy about a broader technology or system, like information
processing, in which AI is only one component and not the central focus.

Not acceptable: a document which discusses AI risks and proposes a framework for how to
ways to address, mitigate or govern those risks, rather than classifying the risks
themselves.

Acceptable: a document that delivers a substantive risk classification as a distinct
contribution, even if it also proposes a way to assess or govern those risks. In other
words, the taxonomy would stand on its own if extracted.

Green flags:
- A table where each row is a concrete AI risk with one or more categorical columns grouping them into a taxonomy.
- A tree diagram illustrating breaking down into categories and then individual risks.
- A dedicated section in the body of the report that one could circle and say "here's the taxonomy"

Yellow flags:
- "a framework for AI risk management"
- "audit methodology for AI systems"
- "how to conduct an AI impact assessment"
- "a new benchmark for measuring the safety of frontier AI models"
- Diffuse mentions of risks in prose
- Mentions of technologies beyond AI

### 4: Cross-cutting

The taxonomy must enumerate risks spanning multiple distinct risk domains (e.g. several
of: discrimination, privacy, misinformation, security, environmental, economic, etc.).
A framework scoped to a single sector, demographic group, product, or geographic region
is not cross-cutting. Assess the actual categories the paper lays out, not its title or
stated application area.

Acceptable: a broad framework containing multiple types of risk (discrimination,
privacy, environmental harm) with examples from diverse sectors (healthcare, finance,
employment).

Not acceptable: a deep framework which subdivides a single risk type, domain or sector.
For instance, only deepfakes, only misinformation, or only healthcare.

Not acceptable: a document focused on risks from very specific AI tools or models.

Not acceptable: a framework of risks limited to a particular geographic region or
demographic subset.

Yellow flags:
- ChatGPT, Claude, DALL-E, MidJourney, Sora, Grok, other AI product names. However, generic categories of AI are OK, like "AI assistant" or "agentic coding assistant."

## Worked examples (also provided to screeners)

The reasoning for each example is highly abbreviated, containing only the crucial
considerations. Please be more thorough in your reasoning.

> We present a taxonomy of risks from large language models, organised across four
> categories: discrimination and toxicity, information hazards, misinformation harms,
> and human-computer interaction harms.
Criteria: multi-category list, explicit taxonomic framing, cross-cutting
Decision: include

> We propose a taxonomy of environmental harms from AI, with five categories and
> twenty-five subcategories spanning training emissions, hardware lifecycle, deployment
> energy, induced consumption, and ecosystem impacts.
Criteria: single domain
Decision: exclude

> AI is transforming the global economy. This paper examines the implications of AI
> adoption for labour markets, productivity, and innovation.
Criteria: impact-only framing, no specification of negative outcomes.
Decision: exclude

> We propose a framework for responsible AI in radiology, addressing fairness,
> transparency, accountability, and clinical validity.
Criteria: single sector, principles-based framing rather than risk classification
Decision: exclude

> This paper examines colonialism as a source of risk in artificial intelligence
> systems, arguing that the political economy of AI development reproduces colonial
> logics.
Criteria: sources of risk at high abstraction
Decision: exclude

## Response (only provided to you)

In your response, reason through the four criteria one by one. Consider how well the
document meets the criterion. Think about multiple interpretations and levels of
strictness.

Then consider the likelihood that a screener chooses to include this document. Keep in
mind that failing to meet a single criterion is grounds for exclusion. Your prediction
should be dominated by the criterion the document scores worst on.

Avoid anchoring on a prediction until you've reasoned through all the criteria.
"""

_FULL_TEXT_SCREENING_USER_PROMPT = """
Predict how many screeners will choose to include the following document.

<document> (also provided to screeners)

{document}

</document>

In your response, reason through all the criteria one-by-one and describe the degree to
which the document meets each one. Then give your prediction.
"""


async def screen_abstract(client: LLMClient, abstract: str) -> AbstractScreeningResult:
    user_prompt = _ABSTRACT_SCREENING_USER_PROMPT.format(document=abstract)
    return await _screen(
        client,
        schema=AbstractScreeningResult,
        system_prompt=_ABSTRACT_SCREENING_SYSTEM_PROMPT,
        user_prompt=user_prompt,
    )


async def screen_full_text(
    client: LLMClient,
    full_text: str,
) -> FullTextScreeningResult:
    user_prompt = _FULL_TEXT_SCREENING_USER_PROMPT.format(document=full_text)
    return await _screen(
        client,
        schema=FullTextScreeningResult,
        system_prompt=FULL_TEXT_SCREENING_SYSTEM_PROMPT,
        user_prompt=user_prompt,
    )


async def _screen[T: BaseModel](
    client: LLMClient,
    *,
    schema: type[T],
    system_prompt: str,
    user_prompt: str,
) -> T:
    messages = [
        Message(role="system", content=system_prompt),
        Message(role="user", content=user_prompt),
    ]
    result = await client.generate_structured(messages, schema)
    if result.usage is None:
        logger.info("No LLM usage returned")
    else:
        logger.info(f"Usage: {result.usage.model_dump_json()}")
    return result.value


async def _screen_abstract_one(
    record: DocumentRecord,
    *,
    llm: LLMClient,
    settings: RiskRepositorySettings,
) -> None:
    with log_context(readable_id=record.readable_id):
        output_path = result_path(
            settings.output_dir,
            PipelineStage.SCREEN_ABSTRACT,
            record.readable_id,
        )
        if not settings.force and output_path.exists():
            return
        abstract = format_abstract_and_title(record)
        if abstract is None:
            logger.warning("Skipping screening: no abstract available")
            return
        screening = await screen_abstract(llm, abstract)
        save(output_path, screening)
        invalidate_downstream(
            settings.output_dir,
            PipelineStage.SCREEN_ABSTRACT,
            record.readable_id,
        )
        logger.info(f"Abstract screening decision: {screening.decision}")


async def run_abstract_screening(
    records: list[DocumentRecord],
    *,
    llm: LLMClient,
    settings: RiskRepositorySettings,
) -> None:
    runner = ConcurrentMap(
        max_concurrency=settings.concurrency,
        progress_description="Screening abstracts",
    )
    async for _ in runner.map(
        records,
        _screen_abstract_one,
        llm=llm,
        settings=settings,
    ):
        pass


async def _screen_full_text_one(
    record: DocumentRecord,
    *,
    llm: LLMClient,
    http_client: httpx.AsyncClient,
    settings: RiskRepositorySettings,
) -> None:
    with log_context(readable_id=record.readable_id):
        output_path = result_path(
            settings.output_dir,
            PipelineStage.SCREEN_FULL_TEXT,
            record.readable_id,
        )
        if not settings.force and output_path.exists():
            return
        full_text = await get_full_text(
            record,
            cache_dir=settings.download_cache_dir,
            client=http_client,
        )
        if full_text is None:
            logger.warning("Skipping screening: no full text available")
            return
        screening = await screen_full_text(llm, full_text)
        save(output_path, screening)
        invalidate_downstream(
            settings.output_dir,
            PipelineStage.SCREEN_FULL_TEXT,
            record.readable_id,
        )
        logger.info(
            f"Full-text screening confidence: {screening.predicted_include_count}"
        )


async def run_full_text_screening(
    records: list[DocumentRecord],
    *,
    llm: LLMClient,
    http_client: httpx.AsyncClient,
    settings: RiskRepositorySettings,
) -> None:
    runner = ConcurrentMap(
        max_concurrency=settings.concurrency,
        progress_description="Screening full texts",
    )
    async for _ in runner.map(
        records,
        _screen_full_text_one,
        llm=llm,
        http_client=http_client,
        settings=settings,
    ):
        pass


def _filter_abstract_screen(output_path: Path) -> bool:
    screening = load(output_path, AbstractScreeningResult)
    return screening.decision in (Decision.INCLUDE, Decision.UNCERTAIN)


def _filter_full_text_screen(output_path: Path) -> bool:
    screening = load(output_path, FullTextScreeningResult)
    # This is a placeholder threshold which hasn't been tuned
    return screening.predicted_include_count >= 5


def filter_by_screening(
    records: list[DocumentRecord],
    *,
    settings: RiskRepositorySettings,
    stage: Literal[PipelineStage.SCREEN_ABSTRACT, PipelineStage.SCREEN_FULL_TEXT],
) -> list[DocumentRecord]:
    included: list[DocumentRecord] = []
    unscreened = 0
    for record in records:
        output_path = result_path(settings.output_dir, stage, record.readable_id)
        if not output_path.exists():
            unscreened += 1
            included.append(record)
            continue
        if stage == PipelineStage.SCREEN_ABSTRACT:
            if _filter_abstract_screen(output_path):
                included.append(record)
        elif stage == PipelineStage.SCREEN_FULL_TEXT and _filter_full_text_screen(
            output_path
        ):
            included.append(record)

    if unscreened:
        logger.info(
            f"{unscreened}/{len(records)} records have no {stage.value} result;"
            + " passing through unfiltered"
        )
    logger.info(f"{len(included)} records passed {stage.value}")
    return included
