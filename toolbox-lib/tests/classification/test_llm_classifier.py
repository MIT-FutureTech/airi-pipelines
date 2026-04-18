import pytest

from toolbox.classification import Category, LLMClassifier

from .helpers import FakeLLMClient


class TestLLMClassifier:
    async def test_classify_returns_result(self) -> None:
        client = FakeLLMClient(
            category="Positive",
            reasoning="Clearly positive",
            confidence=0.9,
        )
        categories = [
            Category(name="Positive", description="Positive sentiment"),
            Category(name="Negative", description="Negative sentiment"),
        ]
        classifier = LLMClassifier(
            client=client,
            categories=categories,
            system_prompt="Classify sentiment.",
        )
        result = await classifier.classify("I love this product!")

        assert result.category == "Positive"
        assert result.reasoning == "Clearly positive"
        assert result.confidence == 0.9

    async def test_system_prompt_is_first_message(self) -> None:
        client = FakeLLMClient(
            category="A",
            reasoning="reason",
            confidence=0.8,
        )
        classifier = LLMClassifier(
            client=client,
            categories=[Category(name="A"), Category(name="B")],
            system_prompt="You are a classifier.",
        )
        await classifier.classify("some text")

        assert client.last_messages[0].role == "system"
        assert client.last_messages[0].content == "You are a classifier."

    async def test_user_message_contains_categories_and_text(self) -> None:
        client = FakeLLMClient(
            category="Cat",
            reasoning="reason",
            confidence=0.8,
        )
        classifier = LLMClassifier(
            client=client,
            categories=[
                Category(name="Cat", description="About cats"),
                Category(name="Dog", description="About dogs"),
            ],
            system_prompt="Classify.",
        )
        await classifier.classify("Meow!")

        user_msg = client.last_messages[1].content
        assert "Cat: About cats" in user_msg
        assert "Dog: About dogs" in user_msg
        assert "Meow!" in user_msg

    async def test_schema_constrains_category_to_enum(self) -> None:
        client = FakeLLMClient(
            category="High",
            reasoning="clearly high",
            confidence=0.9,
        )
        classifier = LLMClassifier(
            client=client,
            categories=[Category(name="High"), Category(name="Low")],
            system_prompt="Classify risk.",
        )
        await classifier.classify("test")

        schema = client.last_schema
        assert schema is not None
        json_schema = schema.model_json_schema()
        # The enum lives in $defs, referenced via $ref from the category field
        assert "$ref" in json_schema["properties"]["category"]
        enum_def = json_schema["$defs"]["CategoryName"]
        assert set(enum_def["enum"]) == {"High", "Low"}

    def test_requires_at_least_two_categories(self) -> None:
        client = FakeLLMClient(
            category="A",
            reasoning="reason",
            confidence=0.8,
        )
        with pytest.raises(ValueError, match="At least two categories"):
            LLMClassifier(
                client=client,
                categories=[Category(name="Only")],
                system_prompt="Classify.",
            )
