"""Stub OCR: a fixed text, no keys and no network.

Features:
    US-SPR-08, F-33, ADR-30
"""

from meritum_core.checks.ocr.errors import OcrUnavailableError
from meritum_core.checks.ocr.image import find_date, inspect_image
from meritum_core.checks.ocr.models import OcrResult
from meritum_core.shared.blobs import BlobStore


class StubOcr:
    """Checks the image like the provider would, then answers with the fixed text.

    Args:
        blobs: The store holding the images.
        text: The answer for every supported image; None fails.

    Features:
        US-SPR-08, F-33, ADR-30
    """

    def __init__(self, blobs: BlobStore, text: str | None) -> None:
        self._blobs = blobs
        self._text = text

    async def read(self, image_id: str) -> OcrResult:
        """Return the fixed text for a supported image.

        Args:
            image_id: The blob id of the image.

        Returns:
            The text, its date candidate and the file metadata.

        Raises:
            UnsupportedImageError: Not a supported image (``inspect_image``).
            OcrUnavailableError: The stub has no text.
            BlobNotFoundError: No image under ``image_id``.
        """  # ruff: ignore[docstring-extraneous-exception]  # raised by inspect_image and the store
        info = inspect_image(await self._blobs.get(image_id))
        if self._text is None:
            msg = "stub has no text fixture"
            raise OcrUnavailableError(msg)
        return OcrResult(
            text=self._text, claim_date=find_date(self._text), metadata=info
        )
