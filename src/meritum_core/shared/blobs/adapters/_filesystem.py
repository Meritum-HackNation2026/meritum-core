"""BlobStore on a directory: the volume shared by backend and worker (ADR-31).

Features:
    US-SPR-11, US-BEZ-05, F-08, F-20, ADR-31
"""

import asyncio
from pathlib import Path

from pydantic import AwareDatetime

from meritum_core.shared.blobs.constants import PARTIAL_SUFFIX
from meritum_core.shared.blobs.errors import BlobNotFoundError
from meritum_core.shared.blobs.models import (
    BlobKind,
    BlobRef,
    check_blob_id,
    new_blob_id,
)


class FilesystemBlobStore:
    """Keeps each blob as one file named by its id, in the configured directory.

    File names come only from ids that passed ``check_blob_id``, and every path is
    checked to stay inside the directory. Retention is not enforced here: the
    workflow that deletes a check's data deletes its blobs (ADR-13).

    Args:
        directory: the volume directory; created if missing.

    Features:
        US-SPR-11, US-BEZ-05, F-08, F-20, ADR-31
    """

    def __init__(self, directory: Path) -> None:
        directory.mkdir(parents=True, exist_ok=True)
        self._directory = directory.resolve()

    def _path(self, blob_id: str) -> Path:
        path = (self._directory / check_blob_id(blob_id)).resolve()
        if path.parent != self._directory:
            raise BlobNotFoundError(blob_id)
        return path

    async def put(
        self,
        data: bytes,
        *,
        kind: BlobKind,
        content_type: str,
        expires_at: AwareDatetime,
    ) -> BlobRef:
        """Write ``data`` to a new file, renamed into place once complete.

        Args:
            data: the file's bytes.
            kind: what the file holds.
            content_type: the MIME type; returned in the ref, not stored.
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
        await asyncio.to_thread(self._write, self._path(ref.blob_id), bytes(data))
        return ref

    @staticmethod
    def _write(path: Path, data: bytes) -> None:
        partial = path.with_name(path.name + PARTIAL_SUFFIX)
        try:
            partial.write_bytes(data)
            partial.replace(path)
        finally:
            partial.unlink(missing_ok=True)

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
            return await asyncio.to_thread(self._path(blob_id).read_bytes)
        except FileNotFoundError:
            raise BlobNotFoundError(blob_id) from None

    async def delete(self, blob_id: str) -> None:
        """Delete a stored file, if present.

        Args:
            blob_id: the id ``put`` returned; a malformed one raises like ``get``.
        """
        await asyncio.to_thread(self._path(blob_id).unlink, missing_ok=True)

    async def uri(self, blob_id: str) -> str:
        """Return the file's ``file://`` address.

        Args:
            blob_id: the id ``put`` returned.

        Returns:
            The absolute file address.

        Raises:
            BlobNotFoundError: No such blob, or ``blob_id`` is malformed.
        """
        path = self._path(blob_id)
        if not await asyncio.to_thread(path.is_file):
            raise BlobNotFoundError(blob_id)
        return path.as_uri()
