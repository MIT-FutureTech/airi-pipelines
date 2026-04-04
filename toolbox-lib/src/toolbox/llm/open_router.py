import os

from toolbox.llm.openai import OpenAIClient

OPEN_ROUTER_BASE_URL = "https://openrouter.ai/api/v1"


class OpenRouterClient(OpenAIClient):
    """LLM client for talking to OpenRouter.

    Usage:

        async with OpenRouterClient(
            model="deepseek/deepseek-r1",
            rate_limit_rps=10,
        ) as client:
            result = await client.generate([Message(role="user", content="Hi")])
    """

    def __init__(
        self,
        *,
        model: str,
        rate_limit_rps: float,
        api_key: str | None = None,
        base_url: str | None = OPEN_ROUTER_BASE_URL,
        timeout: float = 60.0,
        temperature: float | None = None,
        output_token_limit: int | None = None,
    ) -> None:
        if api_key is None:
            api_key = os.environ["OPENROUTER_API_KEY"]
        super().__init__(
            model=model,
            rate_limit_rps=rate_limit_rps,
            api_key=api_key,
            base_url=base_url,
            timeout=timeout,
            temperature=temperature,
            output_token_limit=output_token_limit,
        )
