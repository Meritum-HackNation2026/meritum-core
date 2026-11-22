"""OpenRouter adapter: no data collection, zero retention by default, reported cost.

Reasoning models on OpenRouter reject sampling parameters, so no temperature is
sent; the reasoning effort from settings is.

Features:
    US-WDR-02, US-OBS-02, F-30, ADR-11, ADR-14
"""

import logging
from typing import override

from httpx2 import AsyncClient
from openai import AsyncOpenAI
from pydantic_ai.agent import AgentRunResult
from pydantic_ai.messages import ModelResponse
from pydantic_ai.models.openrouter import (
    OpenRouterModel,
    OpenRouterModelSettings,
    OpenRouterProviderConfig,
)
from pydantic_ai.providers.openrouter import OpenRouterProvider

from meritum_core.shared.llm.constants import (
    OPENROUTER_BASE_URLS,
    OPENROUTER_COST_FIELD,
    OPENROUTER_DATA_COLLECTION,
    OPENROUTER_PINNED_PROVIDERS,
    OPENROUTER_UPSTREAM_FIELD,
)
from meritum_core.shared.llm.settings import LlmProvider, LlmSettings

from ._agent import AgentLlm

_log = logging.getLogger(__name__)


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
        if not settings.openrouter_zdr:
            _log.warning(
                "OpenRouter ZDR is off for %s: golden-set evaluation only, "
                "never user data",
                settings.model,
            )
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
                openrouter_provider=_routing(settings),
            ),
            provider=LlmProvider.OPENROUTER,
            region=settings.region,
        )

    @override
    def _processed_in(self, result: AgentRunResult[object]) -> str:
        details = _details(result)
        upstream = details[-1].get(OPENROUTER_UPSTREAM_FIELD) if details else None
        return f"{self._region}:{upstream}" if upstream else self._region

    @override
    def _cost(self, result: AgentRunResult[object]) -> float:
        costs = (d.get(OPENROUTER_COST_FIELD) for d in _details(result))
        return sum(cost for cost in costs if isinstance(cost, int | float))


def _routing(settings: LlmSettings) -> OpenRouterProviderConfig:
    """Build the ``provider`` routing object of every request.

    Args:
        settings: The openrouter settings.

    Returns:
        No data collection, ZDR as configured, and for a pinned model only its
        providers with fallbacks off.
    """
    routing = OpenRouterProviderConfig(
        zdr=settings.openrouter_zdr, data_collection=OPENROUTER_DATA_COLLECTION
    )
    pinned = OPENROUTER_PINNED_PROVIDERS.get(settings.model)
    if pinned is not None:
        routing["only"] = list(pinned)
        routing["allow_fallbacks"] = False
    return routing


def _details(result: AgentRunResult[object]) -> list[dict[str, object]]:
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
