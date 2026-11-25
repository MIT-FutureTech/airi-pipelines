from collections.abc import Callable, Sequence
from types import TracebackType
from typing import Self, override

from pydantic import BaseModel

from toolbox.llm.client import LLMClient
from toolbox.llm.data_types import Message, StructuredResult, TextResult, TokenUsage

STUB_MODEL = "stub/model"
STUB_USAGE = TokenUsage(input_tokens=11, output_tokens=7)


class StubLLMClient(LLMClient):
    """An LLM client for tests

    Usage:

        client = StubLLMClient(lambda messages: Sentiment(label="positive"))
        result = await client.generate_structured(messages, Sentiment)
        assert client.messages == [messages]
    """

    messages: list[Sequence[Message]]
    _answer: Callable[[Sequence[Message]], BaseModel]

    def __init__(self, answer: Callable[[Sequence[Message]], BaseModel]) -> None:
        self.messages = []
        self._answer = answer

    @override
    async def generate(self, messages: Sequence[Message]) -> TextResult:
        raise NotImplementedError

    @override
    async def generate_structured[T: BaseModel](
        self,
        messages: Sequence[Message],
        schema: type[T],
    ) -> StructuredResult[T]:
        self.messages.append(messages)
        value = self._answer(messages)
        if not isinstance(value, schema):
            raise TypeError(
                f"Expected {schema.__name__} but got {type(value).__name__}"
            )
        return StructuredResult[T](value=value, model=STUB_MODEL, usage=STUB_USAGE)

    @override
    async def close(self) -> None:
        return None

    @override
    async def __aenter__(self) -> Self:
        return self

    @override
    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        return None
