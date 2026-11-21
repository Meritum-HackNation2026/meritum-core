"""Blob store: audio and images shared by backend and worker (ADR-31).

Public API of the concept: re-exports only.

Features:
    US-SPR-11, US-SPR-08, US-BEZ-05, F-08, ADR-31
"""

from meritum_core.shared.blobs.constants import BLOB_ID_PATTERN
from meritum_core.shared.blobs.errors import BlobError, BlobNotFoundError
from meritum_core.shared.blobs.factory import build_blob_store
from meritum_core.shared.blobs.models import BlobKind, BlobRef
from meritum_core.shared.blobs.ports import BlobStore
from meritum_core.shared.blobs.settings import BlobProvider, BlobSettings

__all__ = [
    "BLOB_ID_PATTERN",
    "BlobError",
    "BlobKind",
    "BlobNotFoundError",
    "BlobProvider",
    "BlobRef",
    "BlobSettings",
    "BlobStore",
    "build_blob_store",
]
