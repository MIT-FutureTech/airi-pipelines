from collections.abc import Sequence

import pytest
from pydantic import BaseModel

from toolbox.classification import LLMClassifier
from toolbox.llm import Message, StructuredResult, ToolboxLLMInvalidResponseError
from toolbox.llm.stub import STUB_MODEL, STUB_USAGE, StubLLMClient


class Capital(BaseModel):
    city: str
    country: str


class Sentiment(BaseModel):
    label: str


QUESTION = [Message(role="user", content="What is the capital of France?")]


def _paris(_messages: Sequence[Message]) -> Capital:
    return Capital(city="Paris", country="France")


class TestStubLLMClient:
    async def test_answers_from_the_function(self) -> None:
        client = StubLLMClient(_paris)

        result = await client.generate_structured(QUESTION, Capital)

        assert result == StructuredResult[Capital](
            value=Capital(city="Paris", country="France"),
            model=STUB_MODEL,
            usage=STUB_USAGE,
        )

    async def test_records_what_it_was_sent(self) -> None:
        client = StubLLMClient(_paris)
        other_question = [Message(role="user", content="And of Italy?")]

        await client.generate_structured(QUESTION, Capital)
        await client.generate_structured(other_question, Capital)

        assert client.messages == [QUESTION, other_question]

    async def test_passes_on_errors_from_the_function(self) -> None:
        def fail(_messages: Sequence[Message]) -> Capital:
            raise ToolboxLLMInvalidResponseError("LLM did not generate response")

        client = StubLLMClient(fail)

        with pytest.raises(ToolboxLLMInvalidResponseError):
            await client.generate_structured(QUESTION, Capital)

    async def test_rejects_an_answer_of_the_wrong_type(self) -> None:
        client = StubLLMClient(_paris)

        with pytest.raises(TypeError, match="Expected Sentiment but got Capital"):
            await client.generate_structured(QUESTION, Sentiment)

    async def test_works_as_a_client_for_a_classifier(self) -> None:
        async with StubLLMClient(_paris) as client:
            classifier = LLMClassifier(
                client, system_prompt="Answer briefly.", response_schema=Capital
            )
            result = await classifier.classify("What is the capital of France?")

        assert result.value.city == "Paris"
        assert client.messages[0][0] == Message(
            role="system", content="Answer briefly."
        )
