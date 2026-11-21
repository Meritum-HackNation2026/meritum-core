"""Masking gate settings from ``MERITUM_PII_*``.

Features:
    US-BEZ-04, F-20, ADR-13, ADR-35
"""

from enum import StrEnum
from typing import Self

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from meritum_core.security.pii.constants import (
    DEFAULT_LOCATION,
    ENV_PREFIX,
    EU_LOCATIONS,
)


class PiiGateProvider(StrEnum):
    """Which gate ``build_pii_gate`` builds.

    Features:
        US-BEZ-04, F-20, ADR-13, ADR-35
    """

    NONE = "none"
    SDP = "sdp"


class PiiGateSettings(BaseSettings):
    """Masking gate configuration read from ``MERITUM_PII_*`` variables.

    Attributes:
        gate: ``none`` (default: patterns only, the skip is logged) or ``sdp``
            (Google Sensitive Data Protection).
        project: Google Cloud project billed for Sensitive Data Protection;
            required for ``sdp``.
        location: EU region of the regional endpoint (``EU_LOCATIONS``); checked
            for ``sdp`` only.

    Features:
        US-BEZ-04, F-20, ADR-13, ADR-14, ADR-35
    """

    model_config = SettingsConfigDict(env_prefix=ENV_PREFIX, frozen=True)

    gate: PiiGateProvider = PiiGateProvider.NONE
    project: str | None = Field(default=None, min_length=1)
    location: str = DEFAULT_LOCATION

    @model_validator(mode="after")
    def _sdp_has_a_project(self) -> Self:
        if self.gate is PiiGateProvider.SDP and self.project is None:
            msg = f"{ENV_PREFIX}PROJECT is required for sdp"
            raise ValueError(msg)
        return self

    @model_validator(mode="after")
    def _sdp_runs_in_the_eu(self) -> Self:
        if self.gate is PiiGateProvider.SDP and self.location not in EU_LOCATIONS:
            msg = f"{ENV_PREFIX}LOCATION must be an EU region: {sorted(EU_LOCATIONS)}"
            raise ValueError(msg)
        return self
