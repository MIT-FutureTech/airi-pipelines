from collections.abc import Sequence
from types import TracebackType
from typing import TypeVar

from pydantic import BaseModel

from toolbox.llm.data_types import Message, StructuredResult, TextResult, TokenUsage

T = TypeVar("T", bound=BaseModel)
FAKE_USAGE = TokenUsage(input_tokens=10, output_tokens=20)


class FakeLLMClient:
    _category: str
    _reasoning: str
    _confidence: float

    def __init__(
        self,
        *,
        category: str,
        reasoning: str,
        confidence: float,
    ) -> None:
        self._category = category
        self._reasoning = reasoning
        self._confidence = confidence
        self.last_messages: Sequence[Message] = []
        self.last_schema: type[BaseModel] | None = None

    async def generate(
        self,
        messages: Sequence[Message],
    ) -> TextResult:
        assert messages  # dummy assert to make the messages argument technically used
        return TextResult(text="unused", model="fake", usage=FAKE_USAGE)

    async def generate_structured(
        self,
        messages: Sequence[Message],
        schema: type[T],
    ) -> StructuredResult[T]:
        self.last_messages = messages
        self.last_schema = schema

        value = schema.model_validate(
            {
                "category": self._category,
                "reasoning": self._reasoning,
                "confidence": self._confidence,
            }
        )
        return StructuredResult[T](value=value, model="fake", usage=FAKE_USAGE)

    async def close(self) -> None:
        pass

    async def __aenter__(self) -> "FakeLLMClient":
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        pass
