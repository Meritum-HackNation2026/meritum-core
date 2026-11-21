"""Builds the LLM adapter named by ``MERITUM_LLM_PROVIDER``; nothing else does.

Features:
    US-WDR-02, F-30, ADR-11
"""

from google.auth.credentials import Credentials
from httpx2 import AsyncClient
from pydantic import JsonValue, TypeAdapter

from meritum_core.shared.llm.adapters import OpenRouterLlm, StubLlm, VertexLlm
from meritum_core.shared.llm.ports import LlmPort
from meritum_core.shared.llm.settings import LlmProvider, LlmSettings


def build_llm(
    settings: LlmSettings,
    *,
    credentials: Credentials | None = None,
    http_client: AsyncClient | None = None,
) -> LlmPort:
    """Build the adapter the settings name.

    Args:
        settings: LLM settings, usually ``LlmSettings()`` from the environment.
        credentials: Google credentials for Vertex AI;
            Application Default Credentials when None. Ignored otherwise.
        http_client: HTTP client for the provider (shared pool, or a recorded
            reply in tests); the SDK creates one when None. Ignored by the stub.

    Returns:
        The stub (fixtures from ``stub_fixtures``, none when unset; a file that
        is not a JSON object fails with ValidationError), Gemini on Vertex
        AI or OpenRouter.

    Features:
        US-WDR-02, F-30, ADR-11
    """
    match settings.provider:
        case LlmProvider.VERTEX:
            return VertexLlm(settings, credentials=credentials, http_client=http_client)
        case LlmProvider.OPENROUTER:
            return OpenRouterLlm(settings, http_client=http_client)
        case LlmProvider.STUB:
            path = settings.stub_fixtures
            if path is None:
                return StubLlm({})
            return StubLlm(
                TypeAdapter(dict[str, JsonValue]).validate_json(path.read_bytes())
            )
