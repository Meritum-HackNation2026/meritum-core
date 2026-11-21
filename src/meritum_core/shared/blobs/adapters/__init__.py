"""BlobStore adapters; only ``meritum_core.shared.blobs.factory`` builds them."""

from ._memory import MemoryBlobStore

__all__ = ["MemoryBlobStore"]
