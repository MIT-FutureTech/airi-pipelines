import logging
from collections.abc import Sequence
from types import TracebackType
from typing import Self, TypeVar, cast

from openai import APIConnectionError, APITimeoutError, AsyncOpenAI, RateLimitError
from openai.types import CompletionUsage
from openai.types.chat import ChatCompletionMessageParam
from pydantic import BaseModel
from tenacity import (
    after_log,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from toolbox.llm.data_types import Message, StructuredResult, TextResult, TokenUsage
from toolbox.rate_limit import RateLimiter

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)

_RETRYABLE_EXCEPTIONS = (RateLimitError, APIConnectionError, APITimeoutError)
_GENERATION_RETRY_CONFIG = retry(
    retry=retry_if_exception_type(_RETRYABLE_EXCEPTIONS),
    wait=wait_exponential(multiplier=1, max=30),
    stop=stop_after_attempt(5),
    after=after_log(logger, logging.INFO),
    reraise=True,
)


class ToolboxOpenAIError(ToolboxLLMError):
    pass


class OpenAIClient:
    """LLM client using the OpenAI library.

    Works with OpenAI directly and with OpenAI-compatible APIs like OpenRouter by
    setting a custom base_url.

    Usage:

        async with OpenAIClient(model="gpt-4o", rate_limit_rps=10) as client:
            result = await client.generate([Message(role="user", content="Hi")])
    """

    _model: str
    _temperature: float | None
    _output_token_limit: int | None
    _client: AsyncOpenAI
    _rate_limiter: RateLimiter

    def __init__(
        self,
        *,
        model: str,
        rate_limit_rps: float,
        api_key: str | None = None,
        base_url: str | None = None,
        timeout: float = 60.0,
        temperature: float | None = None,
        output_token_limit: int | None = None,
    ) -> None:
        self._model = model
        self._temperature = temperature
        self._output_token_limit = output_token_limit
        self._client = AsyncOpenAI(
            api_key=api_key,
            base_url=base_url,
            timeout=timeout,
        )
        self._rate_limiter = RateLimiter(rate_limit_rps)

    @_GENERATION_RETRY_CONFIG
    async def generate(
        self,
        messages: Sequence[Message],
    ) -> TextResult:
        if self._rate_limiter:
            await self._rate_limiter.acquire()

        response = await self._client.chat.completions.create(
            model=self._model,
            messages=_to_api_messages(messages),
            temperature=self._temperature,
            max_tokens=self._output_token_limit,
        )

        text = response.choices[0].message.content or ""
        usage = _extract_usage(response.usage)

        return TextResult(text=text, model=self._model, usage=usage)

    @_GENERATION_RETRY_CONFIG
    async def generate_structured(
        self,
        messages: Sequence[Message],
        schema: type[T],
    ) -> StructuredResult[T]:
        if self._rate_limiter:
            await self._rate_limiter.acquire()

        json_schema = schema.model_json_schema()

        response = await self._client.chat.completions.create(
            model=self._model,
            messages=_to_api_messages(messages),
            temperature=self._temperature,
            max_tokens=self._output_token_limit,
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": schema.__name__,
                    "schema": json_schema,
                    "strict": True,
                },
            },
        )

        raw_json = response.choices[0].message.content or ""
        value = schema.model_validate_json(raw_json)
        usage = _extract_usage(response.usage)

        return StructuredResult[T](value=value, model=self._model, usage=usage)

    async def close(self) -> None:
        await self._client.close()

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        await self.close()


def _extract_usage(usage: CompletionUsage | None) -> TokenUsage | None:
    if usage is None:
        return None
    return TokenUsage(
        input_tokens=usage.prompt_tokens,
        output_tokens=usage.completion_tokens,
    )


def _to_api_messages(
    messages: Sequence[Message],
) -> list[ChatCompletionMessageParam]:
    return [
        cast(
            ChatCompletionMessageParam,
            {
                "role": m.role,
                "content": m.content,
            },
        )  # pyright: ignore[reportInvalidCast]
        for m in messages
    ]
