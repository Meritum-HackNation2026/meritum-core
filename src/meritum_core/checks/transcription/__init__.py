"""Transcription of recordings behind ``TranscriptionPort`` (ADR-30).

Public API: the port, its models, limits, errors, settings and the factory.

Features:
    US-SPR-11, F-08, ADR-30
"""

from meritum_core.checks.transcription.audio import inspect_audio
from meritum_core.checks.transcription.constants import (
    MAX_AUDIO_BYTES,
    MAX_AUDIO_SECONDS,
)
from meritum_core.checks.transcription.errors import (
    TranscriptionError,
    TranscriptionUnavailableError,
    UnsupportedAudioError,
)
from meritum_core.checks.transcription.factory import build_transcriber
from meritum_core.checks.transcription.models import AudioFormat, AudioInfo, Transcript
from meritum_core.checks.transcription.ports import TranscriptionPort
from meritum_core.checks.transcription.settings import (
    TranscriptionProvider,
    TranscriptionSettings,
)

__all__ = [
    "MAX_AUDIO_BYTES",
    "MAX_AUDIO_SECONDS",
    "AudioFormat",
    "AudioInfo",
    "Transcript",
    "TranscriptionError",
    "TranscriptionPort",
    "TranscriptionProvider",
    "TranscriptionSettings",
    "TranscriptionUnavailableError",
    "UnsupportedAudioError",
    "build_transcriber",
    "inspect_audio",
]
