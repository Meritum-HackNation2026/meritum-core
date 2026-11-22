"""BlobStore on any S3-compatible bucket: MinIO, Cloudflare R2, a provider's (ADR-31).

Features:
    US-WDR-01, F-30, ADR-31
"""

import asyncio
import contextlib

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError
from pydantic import AwareDatetime

from meritum_core.shared.blobs.constants import S3_MISSING_CODES, S3_URI_SCHEME
from meritum_core.shared.blobs.errors import BlobNotFoundError
from meritum_core.shared.blobs.models import (
    BlobKind,
    BlobRef,
    check_blob_id,
    new_blob_id,
)


def _is_missing(error: ClientError) -> bool:
    return str(error.response.get("Error", {}).get("Code")) in S3_MISSING_CODES


class S3BlobStore:
    """Keeps each blob as one object named by its id in the configured bucket.

    Keys come from the standard ``AWS_ACCESS_KEY_ID`` / ``AWS_SECRET_ACCESS_KEY``
    environment variables, never from settings. No public or signed URLs: readers
    get the bytes or an ``s3://`` address. Retention is the bucket's lifecycle rule;
    ``expires_at`` is not stored per object.

    Args:
        bucket: the private bucket's name.
        endpoint_url: the service endpoint; ``None`` means AWS S3.
        region: the bucket's region; R2 takes ``auto``.

    Features:
        US-WDR-01, F-30, ADR-31
    """

    def __init__(
        self, bucket: str, endpoint_url: str | None = None, region: str | None = None
    ) -> None:
        self._bucket = bucket
        self._client = boto3.client(
            "s3",
            endpoint_url=endpoint_url,
            region_name=region,
            config=Config(s3={"addressing_style": "path"}),
        )

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
        await asyncio.to_thread(
            self._client.put_object,
            Bucket=self._bucket,
            Key=ref.blob_id,
            Body=bytes(data),
            ContentType=content_type,
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
            ClientError: the service failed for another reason (auth, network).
        """
        key = check_blob_id(blob_id)
        try:
            return await asyncio.to_thread(self._read, key)
        except ClientError as error:
            if _is_missing(error):
                raise BlobNotFoundError(blob_id) from None
            raise

    async def delete(self, blob_id: str) -> None:
        """Delete a stored object; S3 deleting a missing key is already a no-op.

        Args:
            blob_id: the id ``put`` returned; a malformed one raises like ``get``.
        """
        key = check_blob_id(blob_id)
        with contextlib.suppress(ClientError):
            await asyncio.to_thread(
                self._client.delete_object, Bucket=self._bucket, Key=key
            )

    async def uri(self, blob_id: str) -> str:
        """Return ``s3://<bucket>/<blob_id>``.

        Args:
            blob_id: the id ``put`` returned.

        Returns:
            The object's S3 address.

        Raises:
            BlobNotFoundError: No such blob, or ``blob_id`` is malformed.
            ClientError: the service failed for another reason (auth, network).
        """
        key = check_blob_id(blob_id)
        try:
            await asyncio.to_thread(
                self._client.head_object, Bucket=self._bucket, Key=key
            )
        except ClientError as error:
            if _is_missing(error):
                raise BlobNotFoundError(blob_id) from None
            raise
        return f"{S3_URI_SCHEME}{self._bucket}/{key}"

    def _read(self, key: str) -> bytes:
        response = self._client.get_object(Bucket=self._bucket, Key=key)
        return bytes(response["Body"].read())
