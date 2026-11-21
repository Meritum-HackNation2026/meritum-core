"""Builds the BlobStore adapter named by ``MERITUM_BLOB_PROVIDER``.

Features:
    ADR-31
"""

from meritum_core.shared.blobs.adapters import MemoryBlobStore
from meritum_core.shared.blobs.ports import BlobStore
from meritum_core.shared.blobs.settings import BlobProvider, BlobSettings


def build_blob_store(settings: BlobSettings) -> BlobStore:
    """Build the adapter the settings name.

    Args:
        settings: the blob store configuration, e.g. ``BlobSettings()`` from env.

    Returns:
        The adapter behind the BlobStore port.

    Features:
        US-SPR-11, US-BEZ-05, ADR-31
    """
    match settings.provider:
        case BlobProvider.MEMORY:
            return MemoryBlobStore()
