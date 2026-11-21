"""Transcription settings from ``MERITUM_TRANSCRIPTION_*``.

Features:
    US-SPR-11, F-08, ADR-30
"""

from enum import StrEnum
from pathlib import Path
from typing import Self

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from meritum_core.checks.transcription.constants import DEFAULT_RETRIES, ENV_PREFIX


class TranscriptionProvider(StrEnum):
    """Which adapter ``build_transcriber`` builds.

    Features:
        US-SPR-11, F-08, ADR-30
    """

    STUB = "stub"
    SPEECH_V2 = "speech_v2"


class TranscriptionSettings(BaseSettings):
    """Transcription configuration read from ``MERITUM_TRANSCRIPTION_*`` variables.

    Model (``chirp_3``), location (``eu``) and language (``pl-PL``) are fixed by
    ADR-30 and live in ``constants.py``.

    Attributes:
        provider: ``stub`` (default, no keys, no network) or ``speech_v2``.
        project: Google Cloud project billed for Speech-to-Text; required for
            ``speech_v2``.
        retries: HTTP attempts per call on transient errors, the first included.
        stub_fixture: JSON file with the stub's ``Transcript``.

    Features:
        US-SPR-11, F-08, ADR-30
    """

    model_config = SettingsConfigDict(env_prefix=ENV_PREFIX, frozen=True)

    provider: TranscriptionProvider = TranscriptionProvider.STUB
    project: str | None = Field(default=None, min_length=1)
    retries: int = Field(default=DEFAULT_RETRIES, ge=1)
    stub_fixture: Path | None = None

    @model_validator(mode="after")
    def _speech_v2_has_a_project(self) -> Self:
        if self.provider is TranscriptionProvider.SPEECH_V2 and self.project is None:
            msg = f"{ENV_PREFIX}PROJECT is required for speech_v2"
            raise ValueError(msg)
        return self
