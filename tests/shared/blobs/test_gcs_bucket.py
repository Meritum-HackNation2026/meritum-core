"""GcsBlobStore on a real bucket: local only (`uv run pytest -m integration`).

Needs Application Default Credentials and ``MERITUM_BLOB_BUCKET``; never runs in CI.
"""

import asyncio
import os
from datetime import UTC, datetime, timedelta

import pytest

from meritum_core.shared.blobs import (
    BlobKind,
    BlobProvider,
    BlobSettings,
    build_blob_store,
)


@pytest.mark.integration
def test_round_trip_on_the_real_bucket(monkeypatch: pytest.MonkeyPatch) -> None:
    bucket = os.environ.get("MERITUM_BLOB_BUCKET", "")
    if not bucket:
        pytest.skip("MERITUM_BLOB_BUCKET is not set")
    monkeypatch.delenv("STORAGE_EMULATOR_HOST", raising=False)
    store = build_blob_store(BlobSettings(provider=BlobProvider.GCS, bucket=bucket))
    expires_at = datetime.now(UTC) + timedelta(days=1)

    async def round_trip() -> None:
        ref = await store.put(
            b"OggS",
            kind=BlobKind.AUDIO,
            content_type="audio/ogg",
            expires_at=expires_at,
        )
        try:
            assert await store.get(ref.blob_id) == b"OggS"
            assert await store.uri(ref.blob_id) == f"gs://{bucket}/{ref.blob_id}"
        finally:
            await store.delete(ref.blob_id)

    asyncio.run(round_trip())
