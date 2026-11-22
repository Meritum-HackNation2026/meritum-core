"""OCR of images behind ``OcrPort``; earlier-hit search behind ``ImageSearchPort``.

Public API: the ports, their models, limits, errors, settings and the factories.

Features:
    US-SPR-08, F-33, ADR-30
"""

from meritum_core.checks.ocr.constants import MAX_IMAGE_BYTES, SUPPORTED_FORMATS
from meritum_core.checks.ocr.errors import (
    ImageTooLargeError,
    OcrError,
    OcrUnavailableError,
    UnsupportedImageError,
    UnsupportedImageFormatError,
)
from meritum_core.checks.ocr.factory import build_image_search, build_ocr
from meritum_core.checks.ocr.image import find_date, inspect_image
from meritum_core.checks.ocr.models import (
    ImageFormat,
    ImageInfo,
    ImageOccurrence,
    ImageSearchResult,
    OcrResult,
)
from meritum_core.checks.ocr.ports import ImageSearchPort, OcrPort
from meritum_core.checks.ocr.settings import OcrProvider, OcrSettings

__all__ = [
    "MAX_IMAGE_BYTES",
    "SUPPORTED_FORMATS",
    "ImageFormat",
    "ImageInfo",
    "ImageOccurrence",
    "ImageSearchPort",
    "ImageSearchResult",
    "ImageTooLargeError",
    "OcrError",
    "OcrPort",
    "OcrProvider",
    "OcrResult",
    "OcrSettings",
    "OcrUnavailableError",
    "UnsupportedImageError",
    "UnsupportedImageFormatError",
    "build_image_search",
    "build_ocr",
    "find_date",
    "inspect_image",
]
