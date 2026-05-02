from collections.abc import Sequence

from pydantic import BaseModel

from toolbox.llm.client import LLMClient
from toolbox.llm.data_types import Message, StructuredResult


class LLMClassifier[T: BaseModel]:
    """Classifies a user prompt into a typed response model using an LLM.

    Usage::

        class Sentiment(BaseModel):
            reasoning: str
            sentiment: Literal["positive", "negative"]

        classifier = LLMClassifier(
            client=my_llm_client,
            system_prompt="Classify the sentiment of the given text.",
            response_schema=Sentiment,
        )
        result = await classifier.classify("I love this product!")
    """

    _client: LLMClient
    _system_prompt: str
    _response_schema: type[T]

    def __init__(
        self,
        client: LLMClient,
        *,
        system_prompt: str,
        response_schema: type[T],
    ) -> None:
        self._client = client
        self._system_prompt = system_prompt
        self._response_schema = response_schema

    async def classify(self, user_prompt: str) -> StructuredResult[T]:
        messages: Sequence[Message] = [
            Message(role="system", content=self._system_prompt),
            Message(role="user", content=user_prompt),
        ]
        return await self._client.generate_structured(messages, self._response_schema)


def format_categories(categories: dict[str, str]) -> str:
    """Format a category-to-description mapping as a markdown list."""
    return "\n".join(
        f"- {name}: {description}" for name, description in categories.items()
    )
