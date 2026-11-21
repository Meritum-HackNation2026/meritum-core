"""Constants of the LLM port.

Features:
    US-WDR-02, F-30, ADR-11
"""

from types import MappingProxyType
from typing import Final

ENV_PREFIX: Final = "MERITUM_LLM_"
"""Prefix of every LLM setting in the environment (US-WDR-02)."""

EU_REGIONS: Final = frozenset(
    {
        "eu",
        "europe-central2",
        "europe-north1",
        "europe-north2",
        "europe-southwest1",
        "europe-west1",
        "europe-west3",
        "europe-west4",
        "europe-west8",
        "europe-west9",
        "europe-west10",
        "europe-west12",
    }
)
"""Vertex AI locations inside the EU (ADR-14); London and Zurich are not."""

DEFAULT_RETRIES: Final = 3
"""HTTP attempts per call, the first included, before ProviderUnavailableError."""

OUTPUT_RETRIES: Final = 1
"""Times the model is re-asked with the validation error when its answer is invalid."""

TEMPERATURE: Final = 0.0
"""Deterministic sampling for every call (ADR-19)."""

STUB_REGION: Final = "local"
"""Region the stub reports in usage: nothing leaves the process."""

DEFAULT_PROVIDER: Final = "openrouter"
"""Provider when ``MERITUM_LLM_PROVIDER`` is unset (Claude is not on our Vertex AI)."""

DEFAULT_MODEL: Final = "anthropic/claude-haiku-5.5"
"""Model when ``MERITUM_LLM_MODEL`` is unset: Claude Haiku 5.5 (US-WDR-02)."""

DEFAULT_REGION: Final = "global"
"""Region when ``MERITUM_LLM_REGION`` is unset: OpenRouter without EU routing."""

DEFAULT_REASONING: Final = "high"
"""Thinking effort when ``MERITUM_LLM_REASONING`` is unset (US-WDR-02)."""

OPENROUTER_BASE_URLS: Final = MappingProxyType(
    {
        "eu": "https://eu.openrouter.ai/api/v1",
        "global": "https://openrouter.ai/api/v1",
    }
)
"""OpenRouter base URL per ``MERITUM_LLM_REGION``; ``eu`` keeps data in Europe."""

OPENROUTER_ZDR: Final = True
"""Default: route OpenRouter calls only to zero-data-retention endpoints (ADR-14)."""

OPENROUTER_COST_FIELD: Final = "cost"
"""Key of the USD cost OpenRouter reports in a response's provider details."""

OPENROUTER_UPSTREAM_FIELD: Final = "downstream_provider"
"""Key of the provider OpenRouter routed the call to, in a response's details."""

OPENROUTER_DATA_COLLECTION: Final = "deny"
"""Skip OpenRouter providers that store or train on prompts (ADR-14)."""

PRICES_USD_PER_MTOK: Final = MappingProxyType(
    {
        "gemini-3.5-flash": (1.65, 9.90),
    }
)
"""Input and output USD per million tokens on Vertex AI in the EU (global price + 10%).

OpenRouter reports each call's cost itself; a model missing here costs 0 (US-OBS-02).
"""

TOKENS_PER_MTOK: Final = 1_000_000
"""Tokens in the unit the price list uses."""
