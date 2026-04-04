from collections.abc import Sequence
from typing import ClassVar, Literal

from pydantic import BaseModel, ConfigDict


class ToolboxLLMError(Exception):
    pass


class Message(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True)

    role: Literal["user", "assistant", "system"]
    content: str


class TokenUsage(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True)

    input_tokens: int
    output_tokens: int


class TextResult(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True)

    text: str
    model: str
    usage: TokenUsage | None


class StructuredResult[T: BaseModel](BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True)

    value: T
    model: str
    usage: TokenUsage | None


Messages = Sequence[Message]
