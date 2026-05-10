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

### 3: Novel Taxonomy

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

Not acceptable: content focused on how organisations or actors should assess, audit or
govern risks from AI rather than classifying AI risks specifically.

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

For your final decision, choose from
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

In your response, reason through all the criteria one-by-one and identify whether or
not the document meets each one. Then give your decision.
"""


def _format_screening_user_prompt(document: str) -> str:
    return _SCREENING_USER_PROMPT.format(document=document)
