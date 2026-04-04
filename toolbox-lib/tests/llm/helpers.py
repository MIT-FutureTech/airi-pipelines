from collections.abc import AsyncGenerator, Sequence
from contextlib import asynccontextmanager
from typing import cast
from unittest.mock import AsyncMock, patch

from openai.types.responses import (
    ParsedResponse,
    ParsedResponseOutputMessage,
    ParsedResponseOutputText,
    Response,
    ResponseOutputMessage,
    ResponseOutputText,
)
from openai.types.responses.response_usage import (
    InputTokensDetails,
    OutputTokensDetails,
    ResponseUsage,
)
from pydantic import BaseModel
from tenacity import Retrying, wait_none

from toolbox.llm.openai import OpenAIClient

FAKE_API_KEY = "sk-fake-key"
FAKE_MODEL = "test-model"


def make_unstructured_response(
    content: str,
    *,
    input_tokens: int = 10,
    output_tokens: int = 20,
) -> Response:
    return Response(
        id="fake-response",
        created_at=0.0,
        model=FAKE_MODEL,
        object="response",
        output=[
            ResponseOutputMessage(
                id="fake-message",
                content=[
                    ResponseOutputText(annotations=[], text=content, type="output_text")
                ],
                role="assistant",
                status="completed",
                type="message",
            ),
        ],
        parallel_tool_calls=False,
        tool_choice="none",
        tools=[],
        usage=ResponseUsage(
            input_tokens=input_tokens,
            input_tokens_details=InputTokensDetails(cached_tokens=0),
            output_tokens=output_tokens,
            output_tokens_details=OutputTokensDetails(reasoning_tokens=0),
            total_tokens=input_tokens + output_tokens,
        ),
    )


def make_structured_response[T: BaseModel](
    response: T,
    *,
    input_tokens: int = 10,
    output_tokens: int = 20,
) -> ParsedResponse[T]:
    return ParsedResponse(
        id="fake-response",
        created_at=0.0,
        model=FAKE_MODEL,
        object="response",
        output=[
            ParsedResponseOutputMessage(
                id="fake-message",
                content=[
                    ParsedResponseOutputText(
                        annotations=[],
                        parsed=response,
                        text=response.model_dump_json(),
                        type="output_text",
                    ),
                ],
                role="assistant",
                status="completed",
                type="message",
            ),
        ],
        parallel_tool_calls=False,
        tool_choice="none",
        tools=[],
        usage=ResponseUsage(
            input_tokens=input_tokens,
            input_tokens_details=InputTokensDetails(cached_tokens=0),
            output_tokens=output_tokens,
            output_tokens_details=OutputTokensDetails(reasoning_tokens=0),
            total_tokens=input_tokens + output_tokens,
        ),
    )


@asynccontextmanager
async def make_mock_openai_client(
    responses: Sequence[Response | Exception],
) -> AsyncGenerator[OpenAIClient]:
    async with OpenAIClient(
        api_key=FAKE_API_KEY,
        model=FAKE_MODEL,
        rate_limit_rps=10.0,
    ) as client:
        mock_create = AsyncMock(side_effect=responses)
        with (
            patch.object(client._client.responses, "create", mock_create),
            patch.object(client._client.responses, "parse", mock_create),
        ):
            # Disable retry waits for fast tests
            for method_name in ("generate", "generate_structured"):
                method = getattr(client, method_name)
                retry = cast(Retrying, method.retry)
                retry.wait = wait_none()
            yield client
