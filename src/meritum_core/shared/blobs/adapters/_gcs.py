"""BlobStore on a private Cloud Storage bucket (ADR-31).

Features:
    US-SPR-11, US-BEZ-05, F-08, F-20, ADR-31
"""

import asyncio

from google.api_core.exceptions import NotFound
from google.cloud.storage import Client
from pydantic import AwareDatetime

from meritum_core.shared.blobs.constants import GCS_URI_SCHEME
from meritum_core.shared.blobs.errors import BlobNotFoundError
from meritum_core.shared.blobs.models import (
    BlobKind,
    BlobRef,
    check_blob_id,
    new_blob_id,
)


class GcsBlobStore:
    """Keeps each blob as one object named by its id in the configured bucket.

    Credentials come from Application Default Credentials (``STORAGE_EMULATOR_HOST``
    points the client at an emulator instead). No public or signed URLs: readers
    get the bytes or a ``gs://`` address. The bucket's lifecycle rule deletes
    objects after 30 days (infra/003); ``expires_at`` is not stored per object.

    Args:
        bucket: the private bucket's name, in europe-central2.

    Features:
        US-SPR-11, US-BEZ-05, F-08, F-20, ADR-31
    """

    def __init__(self, bucket: str) -> None:
        self._bucket = Client().bucket(bucket)

    async def put(
        self,
        data: bytes,
        *,
        kind: BlobKind,
        content_type: str,
        expires_at: AwareDatetime,
    ) -> BlobRef:
        """Upload ``data`` as a new object; never overwrites an existing one.

        Args:
            data: the file's bytes.
            kind: what the file holds.
            content_type: the MIME type, stored as the object's content type.
            expires_at: when the bucket's lifecycle deletes the file at the latest.

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
        blob = self._bucket.blob(ref.blob_id)
        await asyncio.to_thread(
            blob.upload_from_string,
            bytes(data),
            content_type=content_type,
            if_generation_match=0,
        )
        return ref

    async def get(self, blob_id: str) -> bytes:
        """Download a stored object.

        Args:
            blob_id: the id ``put`` returned.

        Returns:
            The stored bytes.

        Raises:
            BlobNotFoundError: No such blob, or ``blob_id`` is malformed.
        """
        blob = self._bucket.blob(check_blob_id(blob_id))
        try:
            return bytes(await asyncio.to_thread(blob.download_as_bytes))
        except NotFound:
            raise BlobNotFoundError(blob_id) from None

    async def delete(self, blob_id: str) -> None:
        """Delete a stored object, if present.

        Args:
            blob_id: the id ``put`` returned; a malformed one raises like ``get``.
        """
        blob = self._bucket.blob(check_blob_id(blob_id))
        try:
            await asyncio.to_thread(blob.delete)
        except NotFound:
            return

    async def uri(self, blob_id: str) -> str:
        """Return ``gs://<bucket>/<blob_id>`` for Speech-to-Text batch (ADR-30).

        Args:
            blob_id: the id ``put`` returned.

        Returns:
            The object's Cloud Storage address.

        Raises:
            BlobNotFoundError: No such blob, or ``blob_id`` is malformed.
        """
        blob = self._bucket.blob(check_blob_id(blob_id))
        if not await asyncio.to_thread(blob.exists):
            raise BlobNotFoundError(blob_id)
        return f"{GCS_URI_SCHEME}{self._bucket.name}/{blob_id}"
