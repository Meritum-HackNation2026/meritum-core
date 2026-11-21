"""Vertex AI adapter for Gemini: temperature 0, thinking level from settings.

Features:
    US-WDR-02, F-30, ADR-11, ADR-14, ADR-19
"""

import logging

from google.auth.credentials import Credentials
from google.genai.types import HttpRetryOptions
from httpx2 import AsyncClient
from pydantic_ai.models.google import GoogleModel
from pydantic_ai.providers.google_cloud import GoogleCloudProvider
from pydantic_ai.settings import ModelSettings

from meritum_core.shared.llm.constants import PRICES_USD_PER_MTOK, TEMPERATURE
from meritum_core.shared.llm.settings import LlmProvider, LlmSettings

from ._agent import AgentLlm

_log = logging.getLogger(__name__)


class VertexLlm(AgentLlm):
    """LlmPort on a Gemini model in a Vertex AI EU location.

    Args:
        settings: Validated vertex settings (EU region).
        credentials: Google credentials; Application Default Credentials when None.
        http_client: HTTP client to use; tests pass one with a recorded reply.

    Features:
        US-WDR-02, F-30, ADR-11, ADR-14, ADR-19
    """

    def __init__(
        self,
        settings: LlmSettings,
        *,
        credentials: Credentials | None = None,
        http_client: AsyncClient | None = None,
    ) -> None:
        if settings.model not in PRICES_USD_PER_MTOK:
            _log.warning("no price for %s: its cost is recorded as 0", settings.model)
        provider = GoogleCloudProvider(
            project=settings.project,
            location=settings.region,
            credentials=credentials,
            http_client=http_client,
            retry_options=HttpRetryOptions(attempts=settings.retries),
        )
        super().__init__(
            GoogleModel(settings.model, provider=provider),
            ModelSettings(temperature=TEMPERATURE, thinking=settings.reasoning),
            provider=LlmProvider.VERTEX,
            region=settings.region,
        )
