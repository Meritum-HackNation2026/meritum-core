"""LLM settings from ``MERITUM_LLM_*``: provider, model, region, reasoning.

Features:
    US-WDR-02, F-30, ADR-11, ADR-14
"""

from enum import StrEnum
from pathlib import Path
from typing import Literal, Self

from pydantic import AliasChoices, Field, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from meritum_core.shared.llm.constants import (
    DEFAULT_MODEL,
    DEFAULT_PROVIDER,
    DEFAULT_REASONING,
    DEFAULT_REGION,
    DEFAULT_RETRIES,
    ENV_PREFIX,
    EU_REGIONS,
    OPENROUTER_BASE_URLS,
    OPENROUTER_ZDR,
)

type Reasoning = Literal["low", "medium", "high"]
"""Thinking effort, mapped by Pydantic AI onto each provider's own parameter."""


class LlmProvider(StrEnum):
    """Which adapter ``build_llm`` builds.

    Features:
        US-WDR-02, F-30, ADR-11
    """

    STUB = "stub"
    VERTEX = "vertex"
    OPENROUTER = "openrouter"


class LlmSettings(BaseSettings):
    """LLM configuration read from ``MERITUM_LLM_*`` environment variables.

    Attributes:
        provider: ``openrouter`` (default), ``vertex`` (Gemini on Vertex AI) or
            ``stub`` (no keys, no network).
        model: Model ID of the provider; Claude Haiku 5.5 on OpenRouter when
            unset (required for ``vertex``).
        region: For ``vertex`` a Vertex AI location in the EU (one of
            ``EU_REGIONS``); for ``openrouter`` ``global`` (default) or ``eu``.
        reasoning: Thinking effort, ``low``, ``medium`` or ``high`` (default).
        project: Google Cloud project; ADC's default project when None.
        retries: HTTP attempts per call on transient errors, the first included.
        stub_fixtures: JSON file mapping an output model's class name to its answer.
        openrouter_api_key: OpenRouter key from ``OPENROUTER_API_KEY``; a secret.
        openrouter_zdr: Zero-data-retention endpoints only (default). Turn off
            only to evaluate a model without them on the golden set, never with
            user data.

    Features:
        US-WDR-02, F-30, ADR-11, ADR-14, ADR-19
    """

    model_config = SettingsConfigDict(env_prefix=ENV_PREFIX, frozen=True)

    provider: LlmProvider = LlmProvider(DEFAULT_PROVIDER)
    model: str = Field(default=DEFAULT_MODEL, min_length=1)
    region: str = Field(default=DEFAULT_REGION, min_length=1)
    reasoning: Reasoning = DEFAULT_REASONING
    project: str | None = None
    retries: int = Field(default=DEFAULT_RETRIES, ge=1)
    stub_fixtures: Path | None = None
    openrouter_api_key: SecretStr | None = Field(
        default=None,
        validation_alias=AliasChoices("OPENROUTER_API_KEY", "openrouter_api_key"),
    )

    openrouter_zdr: bool = OPENROUTER_ZDR

    @model_validator(mode="after")
    def _region_and_key_fit_the_provider(self) -> Self:
        match self.provider:
            case LlmProvider.VERTEX:
                if "model" not in self.model_fields_set:
                    msg = f"{ENV_PREFIX}MODEL is required for vertex"
                    raise ValueError(msg)
                if self.region not in EU_REGIONS:
                    msg = (
                        f"{ENV_PREFIX}REGION must be an EU region, got {self.region!r}"
                    )
                    raise ValueError(msg)
            case LlmProvider.OPENROUTER:
                if self.region not in OPENROUTER_BASE_URLS:
                    msg = f"{ENV_PREFIX}REGION must be eu or global for openrouter"
                    raise ValueError(msg)
                if self.openrouter_api_key is None:
                    msg = "OPENROUTER_API_KEY is required for openrouter"
                    raise ValueError(msg)
            case LlmProvider.STUB:
                pass
        return self
