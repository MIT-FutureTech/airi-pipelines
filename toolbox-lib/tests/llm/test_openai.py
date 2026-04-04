from typing import cast
from unittest.mock import AsyncMock

import pytest
from httpx import Request, Response
from openai import RateLimitError
from pydantic import BaseModel

from toolbox.llm import Message, OpenAIClient
from toolbox.llm.openai import ToolboxOpenAIError

from .helpers import (
    FAKE_MODEL,
    make_mock_openai_client,
    make_structured_response,
    make_unstructured_response,
)


class Sentiment(BaseModel):
    label: str
    score: float


SENTIMENT_RESPONSE = Sentiment(label="positive", score=0.95)


class TestGenerate:
    async def test_returns_text_result(self) -> None:
        response = make_unstructured_response("Hello!", input_tokens=5, output_tokens=2)
        async with make_mock_openai_client([response]) as client:
            result = await client.generate(
                [Message(role="user", content="Hi")],
            )

            assert result.text == "Hello!"
            assert result.model == FAKE_MODEL
            assert result.usage is not None
            assert result.usage.input_tokens == 5
            assert result.usage.output_tokens == 2

    async def test_passes_temperature_and_max_tokens(self) -> None:
        response = make_unstructured_response("ok")
        async with make_mock_openai_client([response]) as client:
            client._temperature = 0.5
            client._output_token_limit = 200
            await client.generate([Message(role="user", content="test")])

            mock_create = cast(AsyncMock, client._client.responses.create)
            call_kwargs = mock_create.call_args.kwargs
            assert call_kwargs["temperature"] == 0.5
            assert call_kwargs["max_output_tokens"] == 200

    async def test_handles_empty_text_string(self) -> None:
        response = make_unstructured_response("")
        async with make_mock_openai_client([response]) as client:
            result = await client.generate(
                [Message(role="user", content="Hi")],
            )

            assert result.text == ""

    async def test_handles_empty_output_list(self) -> None:
        response = make_unstructured_response("")
        response.output = []
        async with make_mock_openai_client([response]) as client:
            result = await client.generate(
                [Message(role="user", content="Hi")],
            )

            assert result.text == ""

    async def test_retries_on_rate_limit(self) -> None:
        error = RateLimitError(
            message="rate limited",
            response=Response(429, request=Request("GET", "https://fake")),
            body=None,
        )
        response = make_unstructured_response("ok")
        async with make_mock_openai_client([error, response]) as client:
            result = await client.generate([Message(role="user", content="Hi")])

            mock_create = cast(AsyncMock, client._client.responses.create)
            assert result.text == "ok"
            assert mock_create.call_count == 2


class TestGenerateStructured:
    async def test_passes_temperature_and_max_tokens(self) -> None:
        response = make_structured_response(SENTIMENT_RESPONSE)
        async with make_mock_openai_client([response]) as client:
            client._temperature = 0.5
            client._output_token_limit = 200
            await client.generate_structured(
                messages=[Message(role="user", content="test")],
                schema=Sentiment,
            )

            mock_create = cast(AsyncMock, client._client.responses.parse)
            call_kwargs = mock_create.call_args.kwargs
            assert call_kwargs["temperature"] == 0.5
            assert call_kwargs["max_output_tokens"] == 200

    async def test_sends_json_schema_response_format(self) -> None:
        response = make_structured_response(SENTIMENT_RESPONSE)
        async with make_mock_openai_client([response]) as client:
            await client.generate_structured(
                messages=[Message(role="user", content="test")],
                schema=Sentiment,
            )

            mock_create = cast(AsyncMock, client._client.responses.parse)
            assert mock_create.call_args.kwargs["text_format"] is Sentiment

    async def test_returns_parsed_model(self) -> None:
        response = make_structured_response(SENTIMENT_RESPONSE)
        async with make_mock_openai_client([response]) as client:
            result = await client.generate_structured(
                [Message(role="user", content="I love this!")],
                Sentiment,
            )

            assert isinstance(result.value, Sentiment)
            assert result.value.label == "positive"
            assert result.value.score == 0.95
            assert result.model == FAKE_MODEL

    async def test_raises_if_parsed_response_is_none(self) -> None:
        response = make_structured_response(SENTIMENT_RESPONSE)
        output0 = response.output[0]
        assert output0.type == "message"
        content0 = output0.content[0]
        assert content0.type == "output_text"
        content0.parsed = None

        async with make_mock_openai_client([response]) as client:
            with pytest.raises(
                ToolboxOpenAIError,
                match="LLM did not generate response",
            ):
                await client.generate_structured(
                    [Message(role="user", content="I love this!")],
                    Sentiment,
                )


class Capital(BaseModel):
    city: str
    country: str


@pytest.mark.network
class TestGenerateNetwork:
    @pytest.fixture
    def client(self) -> OpenAIClient:
        return OpenAIClient(model="gpt-5-nano", rate_limit_rps=1)

    async def test_generate(self, client: OpenAIClient) -> None:
        async with client:
            result = await client.generate(
                [Message(role="user", content="Say hello in one word.")],
            )

        assert "hello" in result.text.lower()
        assert result.model

    async def test_generate_structured(self, client: OpenAIClient) -> None:
        async with client:
            result = await client.generate_structured(
                [Message(role="user", content="What is the capital of France?")],
                schema=Capital,
            )

        assert result.value.city.lower() == "paris"
        assert result.value.country.lower() == "france"
