"""Language model behind ``LlmPort``; the provider is picked by configuration.

Public API: the port and its models, settings, the factory and its error.

Features:
    US-WDR-02, F-30, ADR-11
"""

from meritum_core.shared.llm.errors import ProviderUnavailableError
from meritum_core.shared.llm.factory import build_llm
from meritum_core.shared.llm.ports import LlmPort, LlmResult, LlmUsage, Prompt
from meritum_core.shared.llm.settings import LlmProvider, LlmSettings

__all__ = [
    "LlmPort",
    "LlmProvider",
    "LlmResult",
    "LlmSettings",
    "LlmUsage",
    "Prompt",
    "ProviderUnavailableError",
    "build_llm",
]
