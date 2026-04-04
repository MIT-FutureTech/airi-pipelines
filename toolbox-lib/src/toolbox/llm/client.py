from collections.abc import Sequence
from types import TracebackType
from typing import Protocol, TypeVar

from pydantic import BaseModel

from toolbox.llm.data_types import Message, StructuredResult, TextResult

T = TypeVar("T", bound=BaseModel)


class LLMClient(Protocol):
    async def generate(
        self,
        messages: Sequence[Message],
    ) -> TextResult: ...

    async def generate_structured(
        self,
        messages: Sequence[Message],
        schema: type[T],
    ) -> StructuredResult[T]: ...

    async def close(self) -> None: ...

    async def __aenter__(self) -> "LLMClient": ...

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None: ...
