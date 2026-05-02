from typing import cast
from unittest.mock import AsyncMock

from pydantic import BaseModel

from toolbox.classification import LLMClassifier, format_categories
from toolbox.llm.client import LLMClient
from toolbox.llm.data_types import Message, StructuredResult, TokenUsage

_FAKE_USAGE = TokenUsage(input_tokens=10, output_tokens=20)


class _Sentiment(BaseModel, frozen=True):
    reasoning: str
    sentiment: str


def _make_client(value: BaseModel) -> AsyncMock:
    mock = AsyncMock(spec=LLMClient)
    mock.generate_structured.return_value = StructuredResult(
        value=value,
        model="fake",
        usage=_FAKE_USAGE,
    )
    return mock


class TestLLMClassifier:
    async def test_classify_returns_structured_result(self) -> None:
        sentiment = _Sentiment(reasoning="clearly positive", sentiment="positive")
        mock_client = _make_client(sentiment)
        classifier = LLMClassifier(
            client=cast(LLMClient, mock_client),
            system_prompt="Classify sentiment.",
            response_schema=_Sentiment,
        )
        result = await classifier.classify("I love this product!")

        assert result.value == sentiment
        assert result.model == "fake"

    async def test_classify_sends_system_then_user_message(self) -> None:
        mock_client = _make_client(_Sentiment(reasoning="r", sentiment="positive"))
        classifier = LLMClassifier(
            client=cast(LLMClient, mock_client),
            system_prompt="You are a classifier.",
            response_schema=_Sentiment,
        )
        await classifier.classify("Meow!")

        mock_client.generate_structured.assert_called_once()
        messages, schema = mock_client.generate_structured.call_args.args
        assert messages == [
            Message(role="system", content="You are a classifier."),
            Message(role="user", content="Meow!"),
        ]
        assert schema is _Sentiment


class TestFormatCategories:
    def test_renders_categories_as_markdown_list(self) -> None:
        result = format_categories(
            {
                "Cat": "About cats",
                "Dog": "About dogs",
            }
        )
        assert result == "- Cat: About cats\n- Dog: About dogs"
