"""The transcription port: a stored recording in, its Polish text out.

Features:
    US-SPR-11, F-08, ADR-30
"""

from typing import Protocol, runtime_checkable

from meritum_core.checks.transcription.models import Transcript


@runtime_checkable
class TranscriptionPort(Protocol):
    """Turns a recording from the blob store into text; workflows never see the SDK.

    Features:
        US-SPR-11, F-08, ADR-30, ADR-31
    """

    async def transcribe(self, audio_id: str) -> Transcript:
        """Transcribe the recording stored under ``audio_id``.

        Args:
            audio_id: The blob id ``CheckRequest.audio_id`` carries.

        Returns:
            The transcript in ``pl-PL``.

        Raises:
            UnsupportedAudioError: Not a supported format, or over the limits;
                workflows map it to ``out_of_scope``.
            TranscriptionUnavailableError: The provider failed after retries;
                workflows map it to ``technical_failure``.
            BlobNotFoundError: No recording under ``audio_id``.
        """
        ...
