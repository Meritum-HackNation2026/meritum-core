"""Builds the BlobStore adapter named by ``MERITUM_BLOB_PROVIDER``.

Features:
    ADR-31
"""

from meritum_core.shared.blobs.adapters import (
    FilesystemBlobStore,
    GcsBlobStore,
    MemoryBlobStore,
)
from meritum_core.shared.blobs.constants import ENV_PREFIX
from meritum_core.shared.blobs.errors import BlobError
from meritum_core.shared.blobs.ports import BlobStore
from meritum_core.shared.blobs.settings import BlobProvider, BlobSettings


def build_blob_store(settings: BlobSettings) -> BlobStore:
    """Build the adapter the settings name.

    Args:
        settings: the blob store configuration, e.g. ``BlobSettings()`` from env.

    Returns:
        The adapter behind the BlobStore port.

    Raises:
        BlobError: the provider's directory or bucket is not configured.

    Features:
        US-SPR-11, US-BEZ-05, F-08, F-20, ADR-31
    """
    match settings.provider:
        case BlobProvider.MEMORY:
            return MemoryBlobStore()
        case BlobProvider.FILESYSTEM:
            if settings.directory is None:
                raise BlobError(_missing("directory", settings.provider))
            return FilesystemBlobStore(settings.directory)
        case BlobProvider.GCS:
            if settings.bucket is None:
                raise BlobError(_missing("bucket", settings.provider))
            return GcsBlobStore(settings.bucket)


def _missing(field: str, provider: BlobProvider) -> str:
    return (
        f"{ENV_PREFIX}{field.upper()} is required for {ENV_PREFIX}PROVIDER={provider}"
    )
