"""Constants of the LLM port.

Features:
    US-WDR-02, F-30, ADR-11
"""

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
