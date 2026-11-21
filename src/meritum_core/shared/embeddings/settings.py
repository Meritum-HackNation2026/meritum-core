"""Embeddings settings from ``MERITUM_EMBEDDINGS_*``: provider, model, region.

Features:
    US-KOR-02, F-12, ADR-04, ADR-14
"""

from enum import StrEnum
from typing import Self

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from meritum_core.shared.embeddings.constants import (
    DEFAULT_DIMENSIONS,
    DEFAULT_MODEL,
    DEFAULT_RETRIES,
    ENV_PREFIX,
    EU_REGIONS,
)


class EmbeddingsProvider(StrEnum):
    """Which adapter ``build_embeddings`` builds.

    Features:
        US-KOR-02, F-12, ADR-04
    """

    STUB = "stub"
    VERTEX = "vertex"


class EmbeddingsSettings(BaseSettings):
    """Embeddings configuration read from ``MERITUM_EMBEDDINGS_*`` variables.

    Attributes:
        provider: ``stub`` (default, no keys, no network) or ``vertex``.
        model: Vertex AI embedding model; ``DEFAULT_MODEL`` when unset.
        region: Vertex AI location in the EU, one of ``EU_REGIONS``.
        project: Google Cloud project; ADC's default project when None.
        dimensions: Vector size; the corpus tables are built for the default.
        retries: HTTP attempts per call on transient errors, the first included.

    Features:
        US-KOR-02, F-12, ADR-04, ADR-14
    """

    model_config = SettingsConfigDict(env_prefix=ENV_PREFIX, frozen=True)

    provider: EmbeddingsProvider = EmbeddingsProvider.STUB
    model: str = Field(default=DEFAULT_MODEL, min_length=1)
    region: str | None = Field(default=None, min_length=1)
    project: str | None = None
    dimensions: int = Field(default=DEFAULT_DIMENSIONS, ge=1)
    retries: int = Field(default=DEFAULT_RETRIES, ge=1)

    @model_validator(mode="after")
    def _vertex_is_in_the_eu(self) -> Self:
        if self.provider is not EmbeddingsProvider.VERTEX:
            return self
        if self.region is None:
            msg = f"{ENV_PREFIX}REGION is required for vertex"
            raise ValueError(msg)
        if self.region not in EU_REGIONS:
            msg = f"{ENV_PREFIX}REGION must be an EU region, got {self.region!r}"
            raise ValueError(msg)
        return self
