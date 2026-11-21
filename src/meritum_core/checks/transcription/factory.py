"""Builds the transcription adapter named by ``MERITUM_TRANSCRIPTION_PROVIDER``.

Features:
    US-SPR-11, F-08, ADR-30
"""

from google.auth.credentials import Credentials
from httpx2 import AsyncClient

from meritum_core.checks.transcription.adapters import (
    SpeechV2Transcriber,
    StubTranscriber,
)
from meritum_core.checks.transcription.models import Transcript
from meritum_core.checks.transcription.ports import TranscriptionPort
from meritum_core.checks.transcription.settings import (
    TranscriptionProvider,
    TranscriptionSettings,
)
from meritum_core.shared.blobs import BlobStore


def build_transcriber(
    settings: TranscriptionSettings,
    blobs: BlobStore,
    *,
    credentials: Credentials | None = None,
    http_client: AsyncClient | None = None,
) -> TranscriptionPort:
    """Build the adapter the settings name.

    Args:
        settings: Usually ``TranscriptionSettings()`` from the environment.
        blobs: The store the recordings were uploaded to (ADR-31).
        credentials: Google credentials for Speech-to-Text; Application Default
            Credentials when None. Ignored by the stub.
        http_client: HTTP client for Speech-to-Text (shared pool, or recorded
            replies in tests); a new one when None. Ignored by the stub.

    Returns:
        The stub (transcript from ``stub_fixture``; a file that is not a
        ``Transcript`` fails with ValidationError) or Speech-to-Text v2.

    Features:
        US-SPR-11, F-08, ADR-30
    """
    match settings.provider:
        case TranscriptionProvider.SPEECH_V2:
            return SpeechV2Transcriber(
                settings, blobs, credentials=credentials, http_client=http_client
            )
        case TranscriptionProvider.STUB:
            path = settings.stub_fixture
            if path is None:
                return StubTranscriber(blobs, None)
            transcript = Transcript.model_validate_json(path.read_bytes())
            return StubTranscriber(blobs, transcript)
