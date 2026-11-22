"""OCR settings from ``MERITUM_OCR_*``.

Features:
    US-SPR-08, F-33, ADR-30
"""

from enum import StrEnum
from pathlib import Path
from typing import Self

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from meritum_core.checks.ocr.constants import DEFAULT_RETRIES, ENV_PREFIX


class OcrProvider(StrEnum):
    """Which adapter ``build_ocr`` builds.

    Features:
        US-SPR-08, F-33, ADR-30
    """

    STUB = "stub"
    VISION = "vision"


class OcrSettings(BaseSettings):
    """OCR configuration read from ``MERITUM_OCR_*`` variables.

    Location (``eu``) and feature (``DOCUMENT_TEXT_DETECTION``) are fixed by
    ADR-30 and live in ``constants.py``.

    Attributes:
        provider: ``stub`` (default, no keys, no network) or ``vision``.
        project: Google Cloud project billed for Vision; required for ``vision``.
        retries: HTTP attempts per call on transient errors, the first included.
        stub_text: The text the stub reads from every supported image.

    Features:
        US-SPR-08, F-33, ADR-30
    """

    model_config = SettingsConfigDict(env_prefix=ENV_PREFIX, frozen=True)

    provider: OcrProvider = OcrProvider.STUB
    project: str | None = Field(default=None, min_length=1)
    retries: int = Field(default=DEFAULT_RETRIES, ge=1)
    stub_text: Path | None = None

    @model_validator(mode="after")
    def _vision_has_a_project(self) -> Self:
        if self.provider is OcrProvider.VISION and self.project is None:
            msg = f"{ENV_PREFIX}PROJECT is required for vision"
            raise ValueError(msg)
        return self
