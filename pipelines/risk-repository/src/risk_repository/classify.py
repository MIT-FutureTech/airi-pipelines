import logging
from collections.abc import AsyncGenerator, Iterable, Iterator
from enum import StrEnum
from typing import Self

from pydantic import BaseModel, Field

from risk_repository.extract import ExtractedRisk, ExtractionResult
from risk_repository.records import DocumentRecord
from risk_repository.results import (
    PipelineStage,
    load,
    result_path,
    save,
)
from risk_repository.settings import RiskRepositorySettings
from toolbox.classification import LLMClassifier
from toolbox.concurrency import ConcurrentMap
from toolbox.llm import LLMClient
from toolbox.log import log_context

logger = logging.getLogger(__name__)


class Entity(StrEnum):
    HUMAN = "human"
    AI = "ai"
    OTHER = "other"


class Intent(StrEnum):
    INTENTIONAL = "intentional"
    UNINTENTIONAL = "unintentional"
    OTHER = "other"


class Timing(StrEnum):
    PRE_DEPLOYMENT = "pre-deployment"
    POST_DEPLOYMENT = "post-deployment"
    OTHER = "other"


class CausalClassification(BaseModel):
    reasoning: str = Field(description="Brief explanation for the classification.")
    entity: Entity = Field(description="The entity that causes the risk.")
    intent: Intent = Field(
        description="Whether the risk is an expected or unexpected outcome."
    )
    timing: Timing = Field(
        description="The stage in the AI lifecycle when the risk occurs."
    )


class Subdomain(StrEnum):
    DISCRIMINATION_MISREPRESENTATION = "1.1"
    TOXIC_CONTENT = "1.2"
    UNEQUAL_PERFORMANCE = "1.3"
    PRIVACY_COMPROMISE = "2.1"
    SECURITY_VULNERABILITIES = "2.2"
    FALSE_INFORMATION = "3.1"
    INFORMATION_ECOSYSTEM_POLLUTION = "3.2"
    DISINFORMATION_SURVEILLANCE = "4.1"
    CYBERATTACKS_WEAPONS = "4.2"
    FRAUD_SCAMS_MANIPULATION = "4.3"
    OVERRELIANCE_UNSAFE_USE = "5.1"
    LOSS_OF_AGENCY = "5.2"
    POWER_CENTRALIZATION = "6.1"
    INEQUALITY_EMPLOYMENT = "6.2"
    DEVALUATION_OF_HUMAN_EFFORT = "6.3"
    COMPETITIVE_DYNAMICS = "6.4"
    GOVERNANCE_FAILURE = "6.5"
    ENVIRONMENTAL_HARM = "6.6"
    MISALIGNED_GOALS = "7.1"
    DANGEROUS_CAPABILITIES = "7.2"
    LACK_OF_ROBUSTNESS = "7.3"
    LACK_OF_TRANSPARENCY = "7.4"
    AI_WELFARE_RIGHTS = "7.5"
    MULTI_AGENT_RISKS = "7.6"
    UNCLASSIFIED = "X.1"


class DomainClassification(BaseModel):
    reasoning: str = Field(description="Brief explanation for the classification.")
    subdomain: Subdomain = Field(
        description="The most relevant risk subdomain, given as its code."
    )


class RiskContent(BaseModel, frozen=True):
    """A risk, or one of the enclosing groups in a paper's hierarchy of risks."""

    name: str
    description: str
    supporting_quote: str
    additional_evidence: tuple[str, ...]


class RiskToClassify(RiskContent, frozen=True):
    """A risk and its enclosing groups, ordered outermost first."""

    risk_id: str
    ancestors: tuple[RiskContent, ...]

    @classmethod
    def from_extracted(cls, risk: ExtractedRisk, *, risk_id: str) -> Self:
        """Convert a category/subcategory pair into a tree."""
        if risk.subcategory.strip():
            name = risk.subcategory
            ancestors = (
                RiskContent(
                    name=risk.category,
                    description="",
                    supporting_quote="",
                    additional_evidence=(),
                ),
            )
        else:
            name = risk.category
            ancestors = ()
        return cls(
            risk_id=risk_id,
            name=name,
            description=risk.description,
            supporting_quote=risk.supporting_quote,
            additional_evidence=(),
            ancestors=ancestors,
        )


class ClassifiedRisk(BaseModel):
    risk_id: str
    causal: CausalClassification
    domain: DomainClassification


class ClassificationResult(BaseModel):
    risks: list[ClassifiedRisk]


class DocumentRisks(BaseModel, frozen=True):
    """One document's risks, in extraction order."""

    readable_id: str
    risks: tuple[RiskToClassify, ...]


class ClassifiedDocument(BaseModel):
    readable_id: str
    classification: ClassificationResult


def make_causal_classifier(
    client: LLMClient,
) -> LLMClassifier[CausalClassification]:
    return LLMClassifier(
        client=client,
        system_prompt=CAUSAL_TAXONOMY_SYSTEM_PROMPT,
        response_schema=CausalClassification,
    )


def make_domain_classifier(
    client: LLMClient,
) -> LLMClassifier[DomainClassification]:
    return LLMClassifier(
        client=client,
        system_prompt=DOMAIN_TAXONOMY_SYSTEM_PROMPT,
        response_schema=DomainClassification,
    )


async def classify_risk[T: BaseModel](
    classifier: LLMClassifier[T],
    risk: RiskToClassify,
) -> T:
    user_prompt = format_classification_user_prompt(risk)
    result = await classifier.classify(user_prompt)
    if result.usage is None:
        logger.info("No LLM usage returned")
    else:
        logger.info(f"Usage: {result.usage.model_dump_json()}")
    return result.value


async def _classify_one_risk(
    risk: RiskToClassify,
    *,
    causal_classifier: LLMClassifier[CausalClassification],
    domain_classifier: LLMClassifier[DomainClassification],
) -> ClassifiedRisk:
    with log_context(risk_id=risk.risk_id):
        causal = await classify_risk(causal_classifier, risk)
        domain = await classify_risk(domain_classifier, risk)
        classified = ClassifiedRisk(risk_id=risk.risk_id, causal=causal, domain=domain)
        serialized = classified.model_dump_json(
            exclude={"causal": {"reasoning"}, "domain": {"reasoning"}}
        )
        logger.info(f"Classified risk as {serialized}")
        return classified


async def classify_risks(
    risks: Iterable[RiskToClassify],
    *,
    llm: LLMClient,
    concurrency: int,
    progress_description: str | None,
) -> AsyncGenerator[ClassifiedRisk]:
    """Classify risks concurrently, yielding each verdict as it arrives."""
    causal_classifier = make_causal_classifier(llm)
    domain_classifier = make_domain_classifier(llm)
    runner = ConcurrentMap(
        max_concurrency=concurrency,
        progress_description=progress_description,
    )
    async for classified in runner.map(
        risks,
        _classify_one_risk,
        causal_classifier=causal_classifier,
        domain_classifier=domain_classifier,
    ):
        yield classified


async def classify_documents(
    documents: Iterable[DocumentRisks],
    *,
    llm: LLMClient,
    concurrency: int,
    progress_description: str | None,
) -> AsyncGenerator[ClassifiedDocument]:
    """Classify many documents' risks

    Each document is yielded once all of its risks are classified, with the
    order of its risks preserved.
    """
    outstanding: dict[str, DocumentRisks] = {}
    verdicts: dict[str, dict[str, ClassifiedRisk]] = {}
    owners: dict[str, str] = {}

    def flatten() -> Iterator[RiskToClassify]:
        for document in documents:
            outstanding[document.readable_id] = document
            verdicts[document.readable_id] = {}
            for risk in document.risks:
                owners[risk.risk_id] = document.readable_id
                yield risk

    async for classified in classify_risks(
        risks=flatten(),
        llm=llm,
        concurrency=concurrency,
        progress_description=progress_description,
    ):
        readable_id = owners.pop(classified.risk_id)
        collected = verdicts[readable_id]
        collected[classified.risk_id] = classified
        document = outstanding[readable_id]
        if len(collected) < len(document.risks):
            continue
        del outstanding[readable_id]
        del verdicts[readable_id]
        yield ClassifiedDocument(
            readable_id=readable_id,
            classification=ClassificationResult(
                risks=[collected[risk.risk_id] for risk in document.risks]
            ),
        )

    # Any remaining documents are ones which contain zero risks
    for document in outstanding.values():
        yield ClassifiedDocument(
            readable_id=document.readable_id,
            classification=ClassificationResult(risks=[]),
        )


def _documents_to_classify(
    records: Iterable[DocumentRecord],
    settings: RiskRepositorySettings,
) -> Iterator[DocumentRisks]:
    for record in records:
        with log_context(readable_id=record.readable_id):
            classify_path = result_path(
                settings.output_dir, PipelineStage.CLASSIFY, record.readable_id
            )
            if not settings.force and classify_path.exists():
                continue
            extract_path = result_path(
                settings.output_dir, PipelineStage.EXTRACT, record.readable_id
            )
            if not extract_path.exists():
                logger.warning("Skipping document: no extraction results")
                continue
            extraction = load(extract_path, ExtractionResult)
        yield DocumentRisks(
            readable_id=record.readable_id,
            risks=tuple(
                RiskToClassify.from_extracted(
                    risk, risk_id=f"{record.readable_id}-{i:03}"
                )
                for i, risk in enumerate(extraction.risks)
            ),
        )


async def run_classification(
    records: list[DocumentRecord],
    *,
    llm: LLMClient,
    settings: RiskRepositorySettings,
) -> None:
    async for classified in classify_documents(
        _documents_to_classify(records, settings),
        llm=llm,
        concurrency=settings.concurrency,
        progress_description="Classifying",
    ):
        with log_context(readable_id=classified.readable_id):
            classify_path = result_path(
                settings.output_dir, PipelineStage.CLASSIFY, classified.readable_id
            )
            save(classify_path, classified.classification)
            logger.info(f"Classified {len(classified.classification.risks)} risks")


CAUSAL_TAXONOMY_SYSTEM_PROMPT = """
You are a classifier for the AI Risk Repository, a living database of AI risks
classified according to multiple taxonomies. Your task is to classify an AI risk entry
using the Causal Taxonomy of AI Risks.

The Causal Taxonomy has three independent categories. Assign one value per category.

## Entity

Which entity is presented as the main cause of the risk?

- Human: The risk is caused by a decision or action made by humans, such as choosing poor training data, intentional malicious design, or improper use of AI systems.
- AI: The risk is caused by a decision or action made by an AI system, such as generating harmful content or disempowering humans.
- Other: The focal entity is not clearly a human or AI, or is ambiguous. For example, a risk involving a software toolchain that could be exploited by either humans or AI.

## Intent

Is the risk presented as an expected or unexpected outcome?

- Intentional: The risk occurs as an expected outcome from pursuing a goal, such as AI intentionally programmed to act deceptively or to exhibit bias.
- Unintentional: The risk occurs as an unexpected outcome, such as an AI system inadvertently developing biases due to incomplete training data.
- Other: The intent is not clearly specified, or the risk may occur both intentionally and unintentionally. For example, "The potential for the AI system to infringe upon individuals' rights to privacy."

## Timing

At what stage in the AI lifecycle is the risk presented as occurring?

- Pre-deployment: The risk arises before the AI is fully developed and put into use, such as vulnerabilities in the model due to coding errors.
- Post-deployment: The risk arises after the AI has been trained and deployed for use by end users, including misuse of AI for harmful purposes.
- Other: The risk does not have a clearly defined time of occurrence, or may occur both before and after deployment. For example, "Generative models are known for their substantial energy requirements."

## Additional Instructions

When generating your response, follow the field order of the schema: the first field in the schema should be the first field of your response.
"""

DOMAIN_TAXONOMY_SYSTEM_PROMPT = """
You are a classifier for the AI Risk Repository, a living database of AI risks
classified according to multiple taxonomies. Your task is to classify an AI risk entry
using the Domain Taxonomy of AI Risks.

The Domain Taxonomy organizes risks into seven domains, further divided into 24
subdomains. Assign the single most relevant subdomain. A risk may touch several
subdomains; choose the one that best captures the risk as the authors present it, and
respond with that subdomain's code (e.g. "3.1").

## 1. Discrimination & toxicity

- 1.1 Unfair discrimination and misrepresentation: Unequal treatment of individuals or groups by AI, often based on race, gender, or other sensitive characteristics, resulting in unfair outcomes and representation of those groups.
- 1.2 Exposure to toxic content: AI that exposes users to harmful, abusive, unsafe, or inappropriate content, such as hate speech, violence, extremism, illegal acts, or child sexual abuse material, as well as content that violates community norms such as profanity, inflammatory political speech, or pornography.
- 1.3 Unequal performance across groups: Accuracy and effectiveness of AI decisions and actions depend on group membership, where AI system design and biased training data lead to unequal outcomes, reduced benefits, increased effort, and alienation of users.

## 2. Privacy & security

- 2.1 Compromise of privacy by obtaining, leaking, or correctly inferring sensitive information: AI systems that memorize and leak sensitive personal data or infer private information about individuals without their consent, compromising user expectation of privacy, assisting identity theft, or causing loss of confidential intellectual property.
- 2.2 AI system security vulnerabilities and attacks: Vulnerabilities that can be exploited in AI systems, software development toolchains, and hardware, resulting in unauthorized access, data and privacy breaches, or system manipulation causing unsafe outputs or behavior.

## 3. Misinformation

- 3.1 False or misleading information: AI systems that inadvertently generate or spread incorrect or deceptive information, which can lead to inaccurate beliefs and undermine autonomy. Humans who make decisions based on false beliefs can experience physical, emotional, or material harms.
- 3.2 Pollution of information ecosystem and loss of consensus reality: Highly personalized AI-generated misinformation that creates "filter bubbles" where individuals only see what matches their existing beliefs, undermining shared reality and weakening social cohesion and political processes.

## 4. Malicious actors & misuse

- 4.1 Disinformation, surveillance, and influence at scale: Using AI to conduct large-scale disinformation campaigns, malicious surveillance, or targeted and sophisticated automated censorship and propaganda, with the aim of manipulating political processes, public opinion, and behavior.
- 4.2 Cyberattacks, weapon development or use, and mass harm: Using AI to develop cyber weapons or malware, develop new or enhance existing weapons (e.g. Lethal Autonomous Weapons or chemical, biological, radiological, nuclear, and high-yield explosives), or use weapons to cause mass harm.
- 4.3 Fraud, scams, and targeted manipulation: Using AI to gain a personal advantage over others through cheating, fraud, scams, blackmail, or targeted manipulation of beliefs or behavior, such as AI-facilitated plagiarism, impersonation for illegitimate financial benefit, or creating humiliating or sexual imagery.

## 5. Human-computer interaction

- 5.1 Overreliance and unsafe use: Anthropomorphizing, trusting, or relying on AI systems, leading to emotional or material dependence and inappropriate relationships with or expectations of AI. Trust can be exploited by malicious actors or result in harm from inappropriate use of AI in critical situations.
- 5.2 Loss of human agency and autonomy: Humans delegating key decisions to AI systems, or AI systems making decisions that diminish human control and autonomy, potentially leaving humans feeling disempowered or becoming cognitively enfeebled.

## 6. Socioeconomic & environmental harms

- 6.1 Power centralization and unfair distribution of benefits: AI-driven concentration of power and resources within certain entities or groups, especially those who own powerful AI systems, leading to inequitable distribution of benefits and increased societal inequality.
- 6.2 Increased inequality and decline in employment quality: Social and economic inequalities caused by widespread use of AI, such as automating jobs, reducing the quality of employment, or producing exploitative dependencies between workers and employers.
- 6.3 Economic and cultural devaluation of human effort: AI systems reproducing human innovation or creativity (e.g. art, music, writing, coding, invention), destabilizing economic and social systems that rely on human effort and leading to reduced appreciation for human skills and homogenization of cultural experiences.
- 6.4 Competitive dynamics: Competition by AI developers or state-like actors in an AI "race" to maximize strategic or economic advantage, increasing the risk they release unsafe and error-prone systems.
- 6.5 Governance failure: Inadequate regulatory frameworks and oversight mechanisms that fail to keep pace with AI development, leading to ineffective governance and the inability to manage AI risks appropriately.
- 6.6 Environmental harm: The development and operation of AI systems that cause environmental harm through energy consumption of data centers or the materials and carbon footprints associated with AI hardware.

## 7. AI system safety, failures & limitations

- 7.1 AI pursuing its own goals in conflict with human goals or values: AI systems that act in conflict with human goals or values, especially the goals of designers or users. These misaligned behaviors may arise through reward hacking or goal misgeneralization and may result in AI seeking power, self-proliferating, or deceiving.
- 7.2 AI possessing dangerous capabilities: AI systems that develop or access capabilities that increase their potential to cause mass harm, such as deception, weapons development, persuasion and manipulation, cyber-offense, or self-proliferation, whether via malicious actors, misalignment, or failure.
- 7.3 Lack of capability or robustness: AI systems that fail to perform reliably or effectively under varying conditions, exposing them to errors and failures with significant consequences, especially in critical applications or areas requiring moral reasoning.
- 7.4 Lack of transparency or interpretability: Challenges in understanding or explaining the decision-making processes of AI systems, leading to mistrust, difficulty enforcing compliance or accountability, and the inability to identify and correct errors.
- 7.5 AI welfare and rights: Ethical considerations regarding the treatment of potentially sentient AI entities, including their potential rights and welfare as AI systems become more advanced and autonomous.
- 7.6 Multi-agent risks: Risks from multi-agent interactions, due to incentives (which can lead to conflict or collusion) or the structure of multi-agent systems, which can create cascading failures, selection pressures, new security vulnerabilities, and a lack of shared information and trust.

## Unclassified

- X.1: Use only when the entry does not plausibly fit any subdomain above, for example because it does not describe a concrete AI risk. Prefer a specific subdomain whenever one reasonably applies.

## Additional Instructions

When generating your response, follow the field order of the schema: the first field in the schema should be the first field of your response.
"""

_CLASSIFICATION_USER_PROMPT = """\
The following risk was extracted from a paper.

<risk>
{risk}
</risk>

Please reclassify it according to our own taxonomy.
"""

_CLASSIFICATION_CONTEXT = """\
The risk sits inside the authors' own grouping of risks, given below from the outermost
group inward. The grouping indicates how the original authors classified the risk.

<enclosing-groups>
{groups}
</enclosing-groups>

"""

_CLASSIFICATION_GROUP = """\
<group>
{group}
</group>"""


def _format_content(content: RiskContent) -> str:
    """Render a risk or group, omitting the fields its source left empty."""
    lines = [
        f"{label}: {value}"
        for label, value in (
            ("Name", content.name),
            ("Description", content.description),
            ("Supporting quote", content.supporting_quote),
        )
        if value
    ]
    if content.additional_evidence:
        lines.append("Additional evidence:")
        lines.extend(f"- {evidence}" for evidence in content.additional_evidence)
    return "\n".join(lines)


def format_classification_user_prompt(risk: RiskToClassify) -> str:
    prompt = _CLASSIFICATION_USER_PROMPT.format(risk=_format_content(risk))
    if not risk.ancestors:
        return prompt
    groups = "\n".join(
        _CLASSIFICATION_GROUP.format(group=_format_content(ancestor))
        for ancestor in risk.ancestors
    )
    return _CLASSIFICATION_CONTEXT.format(groups=groups) + prompt
