"""Stub transcriber: the fixture's transcript, no keys and no network.

Features:
    US-SPR-11, F-08
"""

from meritum_core.checks.transcription.audio import inspect_audio
from meritum_core.checks.transcription.errors import TranscriptionUnavailableError
from meritum_core.checks.transcription.models import Transcript
from meritum_core.shared.blobs import BlobStore


class StubTranscriber:
    """Checks the recording like the provider would, then answers with the fixture.

    Args:
        blobs: The store holding the recordings.
        transcript: The answer for every supported recording; None fails.

    Features:
        US-SPR-11, F-08
    """

    def __init__(self, blobs: BlobStore, transcript: Transcript | None) -> None:
        self._blobs = blobs
        self._transcript = transcript

    async def transcribe(self, audio_id: str) -> Transcript:
        """Return the fixture for a supported recording.

        Args:
            audio_id: The blob id of the recording.

        Returns:
            The fixture transcript.

        Raises:
            TranscriptionUnavailableError: The stub has no fixture.
        """
        inspect_audio(await self._blobs.get(audio_id))
        if self._transcript is None:
            msg = "stub has no transcript fixture"
            raise TranscriptionUnavailableError(msg)
        return self._transcript
