"""The OCR and image-search ports: a stored image in, text or earlier hits out.

Features:
    US-SPR-08, F-33, ADR-30
"""

from typing import Protocol, runtime_checkable

from meritum_core.checks.ocr.models import ImageSearchResult, OcrResult


@runtime_checkable
class OcrPort(Protocol):
    """Reads text and a date from a blob-store image; workflows never see the SDK.

    Features:
        US-SPR-08, F-33, ADR-30, ADR-31
    """

    async def read(self, image_id: str) -> OcrResult:
        """Read the text of the image stored under ``image_id``.

        Args:
            image_id: The blob id ``CheckRequest.image_id`` carries.

        Returns:
            The text, the date candidate and the file metadata.

        Raises:
            UnsupportedImageError: Not a supported image, or over the size limit;
                workflows map it to ``out_of_scope``.
            OcrUnavailableError: The provider failed after retries; workflows
                map it to ``technical_failure``.
            BlobNotFoundError: No image under ``image_id``.
        """
        ...


@runtime_checkable
class ImageSearchPort(Protocol):
    """Looks for earlier appearances of an image.

    Features:
        US-SPR-08, F-33, ADR-30
    """

    async def search(self, image_id: str) -> ImageSearchResult:
        """Search for earlier appearances of the image.

        Args:
            image_id: The blob id of the image.

        Returns:
            The occurrences, or ``searched=False`` when no search is configured;
            the answer then says nothing was searched (limitation
            ``image_search_not_run``).
        """
        ...
