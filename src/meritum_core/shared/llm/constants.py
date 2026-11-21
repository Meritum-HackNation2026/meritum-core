"""Constants of the LLM port.

Features:
    US-WDR-02, F-30, ADR-11
"""

from typing import Final

ENV_PREFIX: Final = "MERITUM_LLM_"
"""Prefix of every LLM setting in the environment (US-WDR-02)."""

EU_REGION_PREFIX: Final = "europe-"
"""Vertex AI regions in the EU start with this; data stays in the EU (ADR-14)."""

EU_MULTI_REGION: Final = "eu"
"""Vertex AI EU multi-region endpoint, also allowed by ADR-14."""

DEFAULT_RETRIES: Final = 3
"""Attempts per call, the first included, before ProviderUnavailableError (F-30)."""

TEMPERATURE: Final = 0.0
"""Deterministic sampling for every call (ADR-19)."""

STUB_REGION: Final = "local"
"""Region the stub reports in usage: nothing leaves the process."""
