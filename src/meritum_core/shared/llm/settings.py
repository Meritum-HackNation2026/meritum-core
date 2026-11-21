"""LLM settings from ``MERITUM_LLM_*``: provider, model, region, nothing in code.

Features:
    US-WDR-02, F-30, ADR-11, ADR-14
"""

from enum import StrEnum
from pathlib import Path
from typing import Self

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from meritum_core.shared.llm.constants import (
    DEFAULT_RETRIES,
    ENV_PREFIX,
    EU_MULTI_REGION,
    EU_REGION_PREFIX,
)


class LlmProvider(StrEnum):
    """Which adapter ``build_llm`` builds.

    Features:
        US-WDR-02, F-30
    """

    STUB = "stub"
    VERTEX = "vertex"


class LlmSettings(BaseSettings):
    """LLM configuration read from ``MERITUM_LLM_*`` environment variables.

    Attributes:
        provider: ``stub`` (default, no keys, no network) or ``vertex``.
        model: Pinned model version, e.g. a dated Gemini or Model Garden name.
        region: Vertex AI region in the EU (``europe-*`` or ``eu``).
        project: Google Cloud project; ADC's default project when None.
        retries: Attempts per call, the first included.
        stub_fixtures: JSON file mapping an output model's class name to its answer.

    Features:
        US-WDR-02, F-30, ADR-11, ADR-14, ADR-19
    """

    model_config = SettingsConfigDict(env_prefix=ENV_PREFIX, frozen=True)

    provider: LlmProvider = LlmProvider.STUB
    model: str | None = Field(default=None, min_length=1)
    region: str | None = Field(default=None, min_length=1)
    project: str | None = None
    retries: int = Field(default=DEFAULT_RETRIES, ge=1)
    stub_fixtures: Path | None = None

    @model_validator(mode="after")
    def _vertex_is_pinned_and_in_the_eu(self) -> Self:
        if self.provider is not LlmProvider.VERTEX:
            return self
        if self.model is None or self.region is None:
            msg = "MERITUM_LLM_MODEL and MERITUM_LLM_REGION are required for vertex"
            raise ValueError(msg)
        in_eu = self.region == EU_MULTI_REGION or self.region.startswith(
            EU_REGION_PREFIX
        )
        if not in_eu:
            msg = f"MERITUM_LLM_REGION must be an EU region, got {self.region!r}"
            raise ValueError(msg)
        return self
