from pydantic import BaseModel

from toolbox.classification import LLMClassifier, format_categories

from .helpers import FakeLLMClient


class _Sentiment(BaseModel, frozen=True):
    reasoning: str
    sentiment: str


class TestLLMClassifier:
    async def test_classify_returns_structured_result(self) -> None:
        client = FakeLLMClient(
            payload={"reasoning": "clearly positive", "sentiment": "positive"}
        )
        classifier = LLMClassifier(
            client=client,
            system_prompt="Classify sentiment.",
            response_schema=_Sentiment,
        )
        result = await classifier.classify("I love this product!")

        assert result.value.sentiment == "positive"
        assert result.value.reasoning == "clearly positive"
        assert result.model == "fake"

    async def test_classify_sends_system_then_user_message(self) -> None:
        client = FakeLLMClient(payload={"reasoning": "r", "sentiment": "positive"})
        classifier = LLMClassifier(
            client=client,
            system_prompt="You are a classifier.",
            response_schema=_Sentiment,
        )
        await classifier.classify("Meow!")

        assert len(client.last_messages) == 2
        assert client.last_messages[0].role == "system"
        assert client.last_messages[0].content == "You are a classifier."
        assert client.last_messages[1].role == "user"
        assert client.last_messages[1].content == "Meow!"

    async def test_classify_forwards_response_schema(self) -> None:
        client = FakeLLMClient(payload={"reasoning": "r", "sentiment": "positive"})
        classifier = LLMClassifier(
            client=client,
            system_prompt="Classify.",
            response_schema=_Sentiment,
        )
        await classifier.classify("text")

        assert client.last_schema is _Sentiment


class TestFormatCategories:
    def test_renders_categories_as_markdown_list(self) -> None:
        result = format_categories(
            {
                "Cat": "About cats",
                "Dog": "About dogs",
            }
        )
        assert result == "- Cat: About cats\n- Dog: About dogs"
