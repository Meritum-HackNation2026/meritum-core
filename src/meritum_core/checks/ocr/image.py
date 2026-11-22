"""Recognise an image's format from its bytes and find the date written in its text.

The upload's MIME type comes from the user, so the bytes decide.

Features:
    US-SPR-08, F-33, ADR-30
"""

from datetime import date

from meritum_core.checks.ocr.constants import (
    DATE,
    JPEG_MAGIC,
    MAX_IMAGE_BYTES,
    PNG_MAGIC,
    RIFF_MAGIC,
    SUPPORTED_FORMATS,
    WEBP_FORM_OFFSET,
    WEBP_MAGIC,
)
from meritum_core.checks.ocr.errors import (
    ImageTooLargeError,
    UnsupportedImageFormatError,
)
from meritum_core.checks.ocr.models import ImageFormat, ImageInfo


def inspect_image(data: bytes) -> ImageInfo:
    """Return the image's format and size, or reject it.

    Args:
        data: The whole file.

    Returns:
        The format and the size in bytes.

    Raises:
        ImageTooLargeError: Over ``MAX_IMAGE_BYTES``.
        UnsupportedImageFormatError: Not PNG, JPEG or WebP.

    Features:
        US-SPR-08, F-33, ADR-30
    """
    if len(data) > MAX_IMAGE_BYTES:
        msg = f"image size {len(data)} B is over {MAX_IMAGE_BYTES} B"
        raise ImageTooLargeError(msg)
    image_format = _format_of(data)
    if image_format is None:
        formats = ", ".join(sorted(SUPPORTED_FORMATS))
        msg = f"image is not one of {formats}"
        raise UnsupportedImageFormatError(msg)
    return ImageInfo(format=image_format, size_bytes=len(data))


def _format_of(data: bytes) -> ImageFormat | None:
    if data.startswith(PNG_MAGIC):
        return ImageFormat.PNG
    if data.startswith(JPEG_MAGIC):
        return ImageFormat.JPEG
    is_webp = data[WEBP_FORM_OFFSET : WEBP_FORM_OFFSET + 4] == WEBP_MAGIC
    if data.startswith(RIFF_MAGIC) and is_webp:
        return ImageFormat.WEBP
    return None


def find_date(text: str) -> date | None:
    """Return the first valid day.month.year date in ``text``.

    Args:
        text: Text read from an image.

    Returns:
        The date, or None when the text holds none; an impossible one such as
        31.02.2026 is skipped.

    Features:
        US-SPR-08, F-33, ADR-30
    """
    for day, month, year in DATE.findall(text):
        try:
            return date(int(year), int(month), int(day))
        except ValueError:
            continue
    return None
