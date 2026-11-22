"""Constants of OCR: limits, formats and the Cloud Vision setup.

Features:
    US-SPR-08, F-33, ADR-30
"""

import re
from typing import Final

from pydantic import JsonValue

from meritum_core.checks.ocr.models import ImageFormat

MAX_IMAGE_BYTES: Final = 10 * 1024 * 1024
"""Largest image accepted, 10 MiB; larger files are unsupported (US-SPR-08)."""

SUPPORTED_FORMATS: Final = frozenset(ImageFormat)
"""Image formats accepted: PNG, JPEG and WebP (US-SPR-08)."""

PNG_MAGIC: Final = b"\x89PNG\r\n\x1a\n"
"""First eight bytes of a PNG file."""

JPEG_MAGIC: Final = b"\xff\xd8\xff"
"""First bytes of a JPEG file: start of image and a marker."""

RIFF_MAGIC: Final = b"RIFF"
"""First four bytes of a WebP file."""

WEBP_MAGIC: Final = b"WEBP"
"""RIFF form type of a WebP file, at offset 8."""

WEBP_FORM_OFFSET: Final = 8
"""Offset of the RIFF form type."""

DATE: Final = re.compile(r"(?<!\d)(\d{1,2})[.\-/](\d{1,2})[.\-/](\d{4})(?!\d)")
"""A day.month.year date as Poles write it; a dot, hyphen or slash separates."""

VISION_ENDPOINT: Final = "https://eu-vision.googleapis.com/v1/images:annotate"
"""Regional REST endpoint of Cloud Vision for the EU."""

VISION_SCOPES: Final = ("https://www.googleapis.com/auth/cloud-platform",)
"""OAuth scopes the adapter asks Application Default Credentials for."""

VISION_FEATURES: Final[list[JsonValue]] = [{"type": "DOCUMENT_TEXT_DETECTION"}]
"""Dense-text OCR, the right feature for screenshots of posts."""

VISION_LANGUAGE_HINTS: Final[list[JsonValue]] = ["pl"]
"""Language hint of the text on the image."""

ENV_PREFIX: Final = "MERITUM_OCR_"
"""Prefix of every OCR setting in the environment."""

DEFAULT_RETRIES: Final = 3
"""HTTP attempts per call, the first included, before OcrUnavailableError."""

RETRY_BACKOFF_SECONDS: Final = 0.5
"""Pause before the second attempt; it doubles for every next one."""

HTTP_TIMEOUT_SECONDS: Final = 30.0
"""Timeout of one HTTP call to Cloud Vision."""
