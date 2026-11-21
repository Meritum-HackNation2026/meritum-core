"""Port of the blob store: files shared by backend and worker (ADR-31).

Features:
    US-SPR-11, US-SPR-08, US-BEZ-05, F-08, ADR-31
"""

from typing import Protocol

from pydantic import AwareDatetime

from meritum_core.shared.blobs.models import BlobKind, BlobRef


class BlobStore(Protocol):
    """Stores uploaded audio and images for the lifetime of their check (port).

    Every adapter passes the contract test in ``tests/shared/blobs/``.

    Features:
        US-SPR-11, US-SPR-08, US-BEZ-05, F-08, ADR-31
    """

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
            kind: what the file holds; it prefixes the id.
            content_type: the MIME type, e.g. ``audio/ogg``.
            expires_at: when the provider's retention deletes the file at the
                latest (ADR-13).

        Returns:
            The stored file, with its id.

        Raises:
            pydantic.ValidationError: ``expires_at`` is naive or ``content_type``
                is empty; nothing is stored.
        """
        ...

    async def get(self, blob_id: str) -> bytes:
        """Read a stored file.

        Args:
            blob_id: the id ``put`` returned.

        Returns:
            The bytes given to ``put``.

        Raises:
            BlobNotFoundError: No such blob, or ``blob_id`` is malformed.
        """
        ...

    async def delete(self, blob_id: str) -> None:
        """Delete a stored file; deleting a missing one does nothing.

        Args:
            blob_id: the id ``put`` returned.

        Raises:
            BlobNotFoundError: ``blob_id`` is malformed.
        """
        ...

    async def uri(self, blob_id: str) -> str:
        """Address for providers that read the file from storage themselves.

        Example: ``gs://`` for Speech-to-Text batch recognition (ADR-30).

        Args:
            blob_id: the id ``put`` returned.

        Returns:
            The provider address of the file; it ends with ``blob_id``.

        Raises:
            BlobNotFoundError: No such blob, or ``blob_id`` is malformed.
        """
        ...
