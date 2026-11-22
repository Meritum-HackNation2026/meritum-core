"""Errors of the OCR port; each maps to one check status.

Features:
    US-SPR-08, F-33, ADR-30
"""

from typing import ClassVar

from meritum_core.checks.contracts import CheckStatus, LimitationCode


class OcrError(Exception):
    """Base error of the OCR port and its adapters.

    Features:
        US-SPR-08, F-33, ADR-30
    """


class UnsupportedImageError(OcrError):
    """Not a supported image: unknown format or over the size limit.

    Workflows map it to ``out_of_scope`` with ``out_of_scope_code: "image"``;
    retrying cannot help.

    Attributes:
        check_status: The check status a workflow reports for it.
        limitation_code: The code a workflow puts in ``limitation_codes``;
            each subtype sets it.

    Features:
        US-SPR-08, F-33, ADR-30
    """

    check_status: ClassVar[CheckStatus] = "out_of_scope"
    limitation_code: ClassVar[LimitationCode]


class UnsupportedImageFormatError(UnsupportedImageError):
    """Not PNG, JPEG or WebP.

    Attributes:
        limitation_code: The code a workflow puts in ``limitation_codes``.

    Features:
        US-SPR-08, F-33, ADR-30
    """

    limitation_code: ClassVar[LimitationCode] = "image_format_unsupported"


class ImageTooLargeError(UnsupportedImageError):
    """Over ``MAX_IMAGE_BYTES``.

    Attributes:
        limitation_code: The code a workflow puts in ``limitation_codes``.

    Features:
        US-SPR-08, F-33, ADR-30
    """

    limitation_code: ClassVar[LimitationCode] = "image_too_large"


class OcrUnavailableError(OcrError):
    """The provider failed after all retries or refused the credentials.

    Workflows map it to ``technical_failure``.

    Attributes:
        check_status: The check status a workflow reports for it.

    Features:
        US-SPR-08, F-33, ADR-30
    """

    check_status: ClassVar[CheckStatus] = "technical_failure"
