"""OpenRouter adapter: no data collection, zero retention by default, reported cost.

Reasoning models on OpenRouter reject sampling parameters, so no temperature is
sent; the reasoning effort from settings is.

Features:
    US-WDR-02, US-OBS-02, F-30, ADR-11, ADR-14
"""

from typing import override

from httpx2 import AsyncClient
from openai import AsyncOpenAI
from pydantic import BaseModel
from pydantic_ai.agent import AgentRunResult
from pydantic_ai.messages import ModelResponse
from pydantic_ai.models.openrouter import OpenRouterModel, OpenRouterModelSettings
from pydantic_ai.providers.openrouter import OpenRouterProvider

from meritum_core.shared.llm.constants import (
    OPENROUTER_BASE_URLS,
    OPENROUTER_COST_FIELD,
    OPENROUTER_DATA_COLLECTION,
    OPENROUTER_UPSTREAM_FIELD,
)
from meritum_core.shared.llm.settings import LlmProvider, LlmSettings

from ._agent import AgentLlm


class OpenRouterLlm(AgentLlm):
    """LlmPort on a model routed by OpenRouter to providers that keep no data.

    Args:
        settings: Validated openrouter settings (key set, region eu or global).
        http_client: HTTP client to use; tests pass one with a recorded reply.

    Raises:
        ValueError: The settings carry no OpenRouter key.

    Features:
        US-WDR-02, US-OBS-02, F-30, ADR-11, ADR-14
    """

    def __init__(
        self, settings: LlmSettings, *, http_client: AsyncClient | None = None
    ) -> None:
        key = settings.openrouter_api_key
        if key is None:  # never let the SDK fall back to OPENAI_API_KEY
            msg = "OPENROUTER_API_KEY is required for openrouter"
            raise ValueError(msg)
        client = AsyncOpenAI(
            base_url=OPENROUTER_BASE_URLS[settings.region],
            api_key=key.get_secret_value(),
            max_retries=settings.retries - 1,
            http_client=http_client,
        )
        super().__init__(
            OpenRouterModel(
                settings.model, provider=OpenRouterProvider(openai_client=client)
            ),
            OpenRouterModelSettings(
                thinking=settings.reasoning,
                openrouter_provider={
                    "zdr": settings.openrouter_zdr,
                    "data_collection": OPENROUTER_DATA_COLLECTION,
                },
            ),
            provider=LlmProvider.OPENROUTER,
            region=settings.region,
        )

    @override
    def _processed_in(self, result: AgentRunResult[BaseModel]) -> str:
        details = _details(result)
        upstream = details[-1].get(OPENROUTER_UPSTREAM_FIELD) if details else None
        return f"{self._region}:{upstream}" if upstream else self._region

    @override
    def _cost(self, result: AgentRunResult[BaseModel]) -> float:
        costs = (d.get(OPENROUTER_COST_FIELD) for d in _details(result))
        return sum(cost for cost in costs if isinstance(cost, int | float))


def _details(result: AgentRunResult[BaseModel]) -> list[dict[str, object]]:
    """Collect the provider details of each model response in the run.

    Args:
        result: The finished agent run.

    Returns:
        One mapping per model response, oldest first; empty when none.
    """
    return [
        message.provider_details or {}
        for message in result.new_messages()
        if isinstance(message, ModelResponse)
    ]
