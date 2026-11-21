"""Errors of the transcription port; each maps to one check status.

Features:
    US-SPR-11, F-08, ADR-30
"""

from typing import ClassVar

from meritum_core.checks.contracts import CheckStatus


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

    Features:
        US-SPR-11, F-08, ADR-30
    """

    check_status: ClassVar[CheckStatus] = "out_of_scope"


class TranscriptionUnavailableError(TranscriptionError):
    """The provider failed after all retries or refused the credentials.

    Workflows map it to ``technical_failure``.

    Attributes:
        check_status: The check status a workflow reports for it.

    Features:
        US-SPR-11, F-08, ADR-30
    """

    check_status: ClassVar[CheckStatus] = "technical_failure"
