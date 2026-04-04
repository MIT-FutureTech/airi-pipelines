import pytest
from pydantic import BaseModel

from toolbox.llm import Message, OpenRouterClient


class Capital(BaseModel):
    city: str
    country: str


@pytest.mark.network
class TestGenerateNetwork:
    @pytest.fixture
    def client(self) -> OpenRouterClient:
        return OpenRouterClient(
            model="openai/gpt-5-nano",
            rate_limit_rps=1,
        )

    async def test_generate(self, client: OpenRouterClient) -> None:
        async with client:
            result = await client.generate(
                [Message(role="user", content="Say hello in one word.")],
            )

        assert "hello" in result.text.lower()
        assert result.model

    async def test_generate_structured(self, client: OpenRouterClient) -> None:
        async with client:
            result = await client.generate_structured(
                [Message(role="user", content="What is the capital of France?")],
                schema=Capital,
            )

        assert result.value.city.lower() == "paris"
        assert result.value.country.lower() == "france"
