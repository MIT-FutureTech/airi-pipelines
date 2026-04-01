from collections.abc import AsyncGenerator, Sequence
from contextlib import asynccontextmanager
from typing import cast
from unittest.mock import AsyncMock, patch

from openai.types.chat import ChatCompletion, ChatCompletionMessage
from openai.types.chat.chat_completion import Choice
from openai.types.completion_usage import CompletionUsage
from tenacity import Retrying, wait_none

from toolbox.llm.openai import OpenAIClient

FAKE_API_KEY = "sk-fake-key"
FAKE_MODEL = "test-model"


def make_chat_completion(
    content: str,
    *,
    prompt_tokens: int = 10,
    completion_tokens: int = 20,
) -> ChatCompletion:
    return ChatCompletion(
        id="chatcmpl-fake",
        created=0,
        model=FAKE_MODEL,
        object="chat.completion",
        choices=[
            Choice(
                index=0,
                finish_reason="stop",
                message=ChatCompletionMessage(
                    role="assistant",
                    content=content,
                ),
            ),
        ],
        usage=CompletionUsage(
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=prompt_tokens + completion_tokens,
        ),
    )


@asynccontextmanager
async def make_mock_openai_client(
    responses: Sequence[ChatCompletion | Exception],
) -> AsyncGenerator[OpenAIClient]:
    async with OpenAIClient(
        api_key=FAKE_API_KEY,
        model=FAKE_MODEL,
        rate_limit_rps=10.0,
    ) as client:
        mock_create = AsyncMock(side_effect=responses)
        with patch.object(client._client.chat.completions, "create", mock_create):
            # Disable retry waits for fast tests
            for method_name in ("generate", "generate_structured"):
                method = getattr(client, method_name)
                retry = cast(Retrying, method.retry)
                retry.wait = wait_none()
            yield client
