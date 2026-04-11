from enum import StrEnum

from pydantic import BaseModel, Field

from toolbox.llm import LLMClient, Message

from .extract import ExtractedRisk


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


class ClassifiedRisk(BaseModel):
    risk_id: str
    causal: CausalClassification


class ClassificationResult(BaseModel):
    risks: list[ClassifiedRisk]


async def classify_causal(
    client: LLMClient,
    risk: ExtractedRisk,
) -> CausalClassification:
    messages = [
        Message(role="system", content=CAUSAL_TAXONOMY_SYSTEM_PROMPT),
        Message(role="user", content=format_classification_user_prompt(risk)),
    ]
    result = await client.generate_structured(messages, CausalClassification)
    return result.value


CAUSAL_TAXONOMY_SYSTEM_PROMPT = """
You are a classifier for the AI Risk Repository. Your task is to classify an AI risk
entry using the Causal Taxonomy of AI Risks.

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

_CLASSIFICATION_USER_PROMPT = """\
Classify the following AI risk entry.

<risk>
Category: {category}
Subcategory: {subcategory}
Description: {description}
Supporting quote: {supporting_quote}
</risk>
"""


def format_classification_user_prompt(risk: ExtractedRisk) -> str:
    return _CLASSIFICATION_USER_PROMPT.format(
        category=risk.category,
        subcategory=risk.subcategory,
        description=risk.description,
        supporting_quote=risk.supporting_quote,
    )
