"""Transcription adapters, built only by ``meritum_core.checks.transcription.factory``.

Features:
    US-SPR-11, F-08, ADR-30
"""

from ._speech_v2 import SpeechV2Transcriber
from ._stub import StubTranscriber

__all__ = ["SpeechV2Transcriber", "StubTranscriber"]
