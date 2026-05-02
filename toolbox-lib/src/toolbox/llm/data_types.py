from collections.abc import Sequence
from typing import Literal

from pydantic import BaseModel


class ToolboxLLMError(Exception):
    pass


class Message(BaseModel, frozen=True):
    role: Literal["user", "assistant", "system"]
    content: str


class TokenUsage(BaseModel, frozen=True):
    input_tokens: int
    output_tokens: int


class TextResult(BaseModel, frozen=True):
    text: str
    model: str
    usage: TokenUsage | None


class StructuredResult[T: BaseModel](BaseModel, frozen=True):
    value: T
    model: str
    usage: TokenUsage | None


Messages = Sequence[Message]
