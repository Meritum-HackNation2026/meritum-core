"""Image search that was not configured: it says so instead of finding nothing.

Features:
    US-SPR-08, F-33, ADR-30
"""

from meritum_core.checks.ocr.models import ImageSearchResult


class NotRunImageSearch:
    """ImageSearchPort for when no search API or local image base exists.

    Features:
        US-SPR-08, F-33, ADR-30
    """

    async def search(self, image_id: str) -> ImageSearchResult:  # ruff: ignore[unused-method-argument, no-self-use]  # port signature
        """Report that no search ran.

        Args:
            image_id: Ignored; nothing is searched.

        Returns:
            ``searched=False`` and no occurrences.
        """
        return ImageSearchResult(searched=False)
