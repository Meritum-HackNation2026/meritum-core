"""In-memory BlobStore: for tests and behave scenarios, one process only.

Features:
    US-SPR-11, US-BEZ-05, ADR-31
"""

from pydantic import AwareDatetime

from meritum_core.shared.blobs.constants import MEMORY_URI_SCHEME
from meritum_core.shared.blobs.errors import BlobNotFoundError
from meritum_core.shared.blobs.models import (
    BlobKind,
    BlobRef,
    check_blob_id,
    new_blob_id,
)


class MemoryBlobStore:
    """BlobStore fake that keeps the bytes in a dict.

    Features:
        US-SPR-11, US-BEZ-05, ADR-31
    """

    def __init__(self) -> None:
        self._blobs: dict[str, bytes] = {}

    async def put(
        self,
        data: bytes,
        *,
        kind: BlobKind,
        content_type: str,
        expires_at: AwareDatetime,
    ) -> BlobRef:
        """Store ``data`` under a new random id.

        Args:
            data: the file's bytes.
            kind: what the file holds.
            content_type: the MIME type.
            expires_at: when the file is deleted at the latest.

        Returns:
            The stored file.
        """
        ref = BlobRef(
            blob_id=new_blob_id(kind),
            kind=kind,
            content_type=content_type,
            size=len(data),
            expires_at=expires_at,
        )
        self._blobs[ref.blob_id] = bytes(data)
        return ref

    async def get(self, blob_id: str) -> bytes:
        """Read a stored file.

        Args:
            blob_id: the id ``put`` returned.

        Returns:
            The stored bytes.

        Raises:
            BlobNotFoundError: No such blob, or ``blob_id`` is malformed.
        """
        try:
            return self._blobs[check_blob_id(blob_id)]
        except KeyError:
            raise BlobNotFoundError(blob_id) from None

    async def delete(self, blob_id: str) -> None:
        """Delete a stored file, if present.

        Args:
            blob_id: the id ``put`` returned; a malformed one raises like ``get``.
        """
        self._blobs.pop(check_blob_id(blob_id), None)

    async def uri(self, blob_id: str) -> str:
        """Return ``memory://<blob_id>``.

        Args:
            blob_id: the id ``put`` returned.

        Returns:
            The fake address.

        Raises:
            BlobNotFoundError: No such blob, or ``blob_id`` is malformed.
        """
        if check_blob_id(blob_id) not in self._blobs:
            raise BlobNotFoundError(blob_id)
        return f"{MEMORY_URI_SCHEME}{blob_id}"
