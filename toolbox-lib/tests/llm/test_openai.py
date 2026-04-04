import json
from typing import cast
from unittest.mock import AsyncMock

import pytest
from httpx import Request, Response
from openai import RateLimitError
from pydantic import BaseModel, ValidationError

from toolbox.llm.data_types import Message

from .helpers import FAKE_MODEL, make_chat_completion, make_mock_openai_client


class Sentiment(BaseModel):
    label: str
    score: float


SENTIMENT_RESPONSE_JSON = json.dumps({"label": "positive", "score": 0.95})


class TestGenerate:
    async def test_returns_text_result(self) -> None:
        completion = make_chat_completion(
            "Hello!", prompt_tokens=5, completion_tokens=2
        )
        async with make_mock_openai_client([completion]) as client:
            result = await client.generate(
                [Message(role="user", content="Hi")],
            )

            assert result.text == "Hello!"
            assert result.model == FAKE_MODEL
            assert result.usage is not None
            assert result.usage.input_tokens == 5
            assert result.usage.output_tokens == 2

    async def test_passes_temperature_and_max_tokens(self) -> None:
        completion = make_chat_completion("ok")
        async with make_mock_openai_client([completion]) as client:
            client._temperature = 0.5
            client._output_token_limit = 200
            await client.generate([Message(role="user", content="test")])

            mock_create = cast(AsyncMock, client._client.chat.completions.create)
            call_kwargs = mock_create.call_args.kwargs
            assert call_kwargs["temperature"] == 0.5
            assert call_kwargs["max_tokens"] == 200

    async def test_handles_none_content(self) -> None:
        completion = make_chat_completion("")
        completion.choices[0].message.content = None
        async with make_mock_openai_client([completion]) as client:
            result = await client.generate(
                [Message(role="user", content="Hi")],
            )

            assert result.text == ""
            assert result.usage is not None

    async def test_retries_on_rate_limit(self) -> None:
        error = RateLimitError(
            message="rate limited",
            response=Response(429, request=Request("GET", "https://fake")),
            body=None,
        )
        completion = make_chat_completion("ok")
        async with make_mock_openai_client([error, completion]) as client:
            result = await client.generate([Message(role="user", content="Hi")])

            mock_create = cast(AsyncMock, client._client.chat.completions.create)
            assert result.text == "ok"
            assert mock_create.call_count == 2


class TestGenerateStructured:
    async def test_passes_temperature_and_max_tokens(self) -> None:
        completion = make_chat_completion(SENTIMENT_RESPONSE_JSON)
        async with make_mock_openai_client([completion]) as client:
            client._temperature = 0.5
            client._output_token_limit = 200
            await client.generate_structured(
                messages=[Message(role="user", content="test")],
                schema=Sentiment,
            )

            mock_create = cast(AsyncMock, client._client.chat.completions.create)
            call_kwargs = mock_create.call_args.kwargs
            assert call_kwargs["temperature"] == 0.5
            assert call_kwargs["max_tokens"] == 200

    async def test_sends_json_schema_response_format(self) -> None:
        completion = make_chat_completion(SENTIMENT_RESPONSE_JSON)

        async with make_mock_openai_client([completion]) as client:
            await client.generate_structured(
                messages=[Message(role="user", content="test")],
                schema=Sentiment,
            )

            mock_create = cast(AsyncMock, client._client.chat.completions.create)
            call_kwargs = mock_create.call_args.kwargs
            rf = call_kwargs["response_format"]
            assert rf["type"] == "json_schema"
            assert rf["json_schema"]["name"] == "Sentiment"
            assert rf["json_schema"]["schema"] == Sentiment.model_json_schema()
            assert rf["json_schema"]["strict"] is True

    async def test_returns_parsed_model(self) -> None:
        completion = make_chat_completion(SENTIMENT_RESPONSE_JSON)

        async with make_mock_openai_client([completion]) as client:
            result = await client.generate_structured(
                [Message(role="user", content="I love this!")],
                Sentiment,
            )

            assert isinstance(result.value, Sentiment)
            assert result.value.label == "positive"
            assert result.value.score == 0.95
            assert result.model == FAKE_MODEL

    async def test_rejects_invalid_json(self) -> None:
        completion = make_chat_completion("As an AI assistant, ...")

        async with make_mock_openai_client([completion]) as client:
            with pytest.raises(ValidationError, match="Invalid JSON"):
                await client.generate_structured(
                    [Message(role="user", content="I love this!")],
                    Sentiment,
                )

    async def test_rejects_noncompliant_json(self) -> None:
        completion = make_chat_completion('{"label": "wrong", "score": "good"}')

        async with make_mock_openai_client([completion]) as client:
            with pytest.raises(ValidationError, match="validation error for Sentiment"):
                await client.generate_structured(
                    [Message(role="user", content="I love this!")],
                    Sentiment,
                )
