from collections.abc import Sequence
from enum import StrEnum

from pydantic import BaseModel, Field, create_model

from toolbox.classification.data_types import Category, ClassificationResult
from toolbox.llm.client import LLMClient
from toolbox.llm.data_types import Message


class LLMClassifier:
    """Classifies text into one of a set of categories using an LLM.

    Usage::

        classifier = LLMClassifier(
            client=my_llm_client,
            categories=[Category(name="Positive"), Category(name="Negative")],
            system_prompt="Classify the sentiment of the given text.",
        )
        result = await classifier.classify("I love this product!")
    """

    _client: LLMClient
    _categories: Sequence[Category]
    _system_prompt: str
    _response_schema: type[BaseModel]

    def __init__(
        self,
        client: LLMClient,
        categories: Sequence[Category],
        *,
        system_prompt: str,
    ) -> None:
        if len(categories) < 2:
            raise ValueError("At least two categories are required")

        self._client = client
        self._categories = categories
        self._system_prompt = system_prompt
        self._response_schema = _build_response_schema(categories)

    async def classify(self, text: str) -> ClassificationResult:
        category_list = _format_categories(self._categories)

        messages = [
            Message(role="system", content=self._system_prompt),
            Message(
                role="user",
                content=(
                    f"## Categories\n{category_list}\n\n## Text to classify\n{text}"
                ),
            ),
        ]

        result = await self._client.generate_structured(
            messages,
            self._response_schema,
        )
        return ClassificationResult.model_validate(result.value.model_dump())


def _build_response_schema(categories: Sequence[Category]) -> type[BaseModel]:
    """Build a Pydantic model whose `category` field is an enum."""
    category_enum = StrEnum("CategoryName", {cat.name: cat.name for cat in categories})
    return create_model(
        "ClassificationResponse",
        reasoning=(str, Field(description="Brief explanation for this classification")),
        category=(category_enum, Field(description="The chosen category")),
        confidence=(
            float,
            Field(
                description="Confidence score between 0 and 1",
                ge=0.0,
                le=1.0,
            ),
        ),
    )


def _format_categories(categories: Sequence[Category]) -> str:
    lines: list[str] = []
    for cat in categories:
        if cat.description:
            lines.append(f"- {cat.name}: {cat.description}")
        else:
            lines.append(f"- {cat.name}")
    return "\n".join(lines)
