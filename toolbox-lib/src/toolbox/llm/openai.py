import json
import logging
from collections.abc import Sequence
from types import TracebackType
from typing import Self, TypeVar

from openai import APIConnectionError, APITimeoutError, AsyncOpenAI, RateLimitError
from openai.types.responses import (
    EasyInputMessageParam,
    ResponseInputParam,
    ResponseUsage,
)
from pydantic import BaseModel, ValidationError
from tenacity import (
    after_log,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from toolbox.llm.data_types import (
    Message,
    StructuredResult,
    TextResult,
    TokenUsage,
    ToolboxLLMInvalidResponseError,
)
from toolbox.rate_limit import RateLimiter

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)

_RETRYABLE_EXCEPTIONS = (
    APIConnectionError,
    APITimeoutError,
    RateLimitError,
    ToolboxLLMInvalidResponseError,
    ValidationError,
)
_GENERATION_RETRY_CONFIG = retry(
    retry=retry_if_exception_type(_RETRYABLE_EXCEPTIONS),
    wait=wait_exponential(multiplier=1, max=30),
    stop=stop_after_attempt(5),
    after=after_log(logger, logging.INFO),
    reraise=True,
)


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

        response = await self._client.responses.create(
            input=_to_api_messages(messages),
            model=self._model,
            temperature=self._temperature,
            max_output_tokens=self._output_token_limit,
            text={"format": {"type": "text"}},
        )
        return TextResult(
            text=response.output_text,
            model=response.model,
            usage=_extract_usage(response.usage),
        )

    @_GENERATION_RETRY_CONFIG
    async def generate_structured(
        self,
        messages: Sequence[Message],
        schema: type[T],
    ) -> StructuredResult[T]:
        if self._rate_limiter:
            await self._rate_limiter.acquire()

        response = await self._client.responses.parse(
            input=_to_api_messages(messages),
            model=self._model,
            temperature=self._temperature,
            max_output_tokens=self._output_token_limit,
            text_format=schema,
        )
        if (value := response.output_parsed) is None:
            serialized_messages = json.dumps(
                [msg.model_dump_json() for msg in messages],
                indent=2,
            )
            logger.debug(
                f"No response from {self._model}: messages={serialized_messages}",
            )
            logger.info(
                f"Could not parse response from {self._model}: {response.model_dump_json(indent=2)}"
            )
            raise ToolboxLLMInvalidResponseError("LLM did not generate response")
        return StructuredResult[T](
            value=value,
            model=response.model,
            usage=_extract_usage(response.usage),
        )

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


def _to_api_messages(messages: Sequence[Message]) -> ResponseInputParam:
    return [
        EasyInputMessageParam(
            {
                "role": m.role,
                "content": m.content,
                "type": "message",
            },
        )
        for m in messages
    ]


def _extract_usage(usage: ResponseUsage | None) -> TokenUsage | None:
    if usage is None:
        return None
    return TokenUsage(
        input_tokens=usage.input_tokens,
        output_tokens=usage.output_tokens,
    )
