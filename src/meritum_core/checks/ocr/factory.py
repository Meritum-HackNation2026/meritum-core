"""Builds the OCR and image-search adapters.

Features:
    US-SPR-08, F-33, ADR-30
"""

from google.auth.credentials import Credentials
from httpx2 import AsyncClient

from meritum_core.checks.ocr.adapters import NotRunImageSearch, StubOcr, VisionOcr
from meritum_core.checks.ocr.ports import ImageSearchPort, OcrPort
from meritum_core.checks.ocr.settings import OcrProvider, OcrSettings
from meritum_core.shared.blobs import BlobStore


def build_ocr(
    settings: OcrSettings,
    blobs: BlobStore,
    *,
    credentials: Credentials | None = None,
    http_client: AsyncClient | None = None,
) -> OcrPort:
    """Build the adapter named by ``MERITUM_OCR_PROVIDER``.

    Args:
        settings: Usually ``OcrSettings()`` from the environment.
        blobs: The store the images were uploaded to (ADR-31).
        credentials: Google credentials for Vision; Application Default
            Credentials when None. Ignored by the stub.
        http_client: HTTP client for Vision (shared pool, or recorded replies
            in tests); a new one when None. Ignored by the stub.

    Returns:
        The stub (text from the ``stub_text`` file) or Cloud Vision in the EU.

    Features:
        US-SPR-08, F-33, ADR-30
    """
    match settings.provider:
        case OcrProvider.VISION:
            return VisionOcr(
                settings, blobs, credentials=credentials, http_client=http_client
            )
        case OcrProvider.STUB:
            path = settings.stub_text
            text = None if path is None else path.read_text(encoding="utf-8")
            return StubOcr(blobs, text)


def build_image_search() -> ImageSearchPort:
    """Build the image search; no provider is wired yet.

    Returns:
        The adapter that answers "not searched" (``image_search_not_run``)
        until a search API or a local image base is chosen.

    Features:
        US-SPR-08, F-33, ADR-30
    """
    return NotRunImageSearch()
