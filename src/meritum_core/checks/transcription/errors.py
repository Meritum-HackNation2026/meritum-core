"""Errors of the transcription port; each maps to one check status.

Features:
    US-SPR-11, F-08, ADR-30
"""

from typing import ClassVar

from meritum_core.checks.contracts import CheckStatus, LimitationCode


class TranscriptionError(Exception):
    """Base error of the transcription port and its adapters.

    Features:
        US-SPR-11, F-08, ADR-30
    """


class UnsupportedAudioError(TranscriptionError):
    """Not a supported recording: unknown format, or over the size or length limit.

    Workflows map it to ``out_of_scope``; retrying cannot help.

    Attributes:
        check_status: The check status a workflow reports for it.
        limitation_code: The code a workflow puts in ``limitation_codes``;
            each subtype sets it.

    Features:
        US-SPR-11, F-08, ADR-30
    """

    check_status: ClassVar[CheckStatus] = "out_of_scope"
    limitation_code: ClassVar[LimitationCode]


class UnsupportedAudioFormatError(UnsupportedAudioError):
    """Not OGG Opus, MP3, M4A or WAV, or no readable length.

    Attributes:
        limitation_code: The code a workflow puts in ``limitation_codes``.

    Features:
        US-SPR-11, F-08, ADR-30
    """

    limitation_code: ClassVar[LimitationCode] = "audio_format_unsupported"


class AudioTooLongError(UnsupportedAudioError):
    """Over ``MAX_AUDIO_SECONDS``, or over ``MAX_AUDIO_BYTES``.

    The size cap counts as length: for the user both mean "recording too long".

    Attributes:
        limitation_code: The code a workflow puts in ``limitation_codes``.

    Features:
        US-SPR-11, F-08, ADR-30
    """

    limitation_code: ClassVar[LimitationCode] = "audio_too_long"


class TranscriptionUnavailableError(TranscriptionError):
    """The provider failed after all retries or refused the credentials.

    Workflows map it to ``technical_failure``.

    Attributes:
        check_status: The check status a workflow reports for it.

    Features:
        US-SPR-11, F-08, ADR-30
    """

    check_status: ClassVar[CheckStatus] = "technical_failure"
