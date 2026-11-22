"""OCR adapters, built only by ``meritum_core.checks.ocr.factory``.

Features:
    US-SPR-08, F-33, ADR-30
"""

from ._no_search import NotRunImageSearch
from ._stub import StubOcr
from ._vision import VisionOcr

__all__ = ["NotRunImageSearch", "StubOcr", "VisionOcr"]
