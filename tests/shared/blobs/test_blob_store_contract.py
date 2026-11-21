"""BlobStore port contract: every adapter in conftest.py must pass these tests."""

import asyncio
import re
from datetime import UTC, datetime, timedelta

import pytest

from meritum_core.shared.blobs import (
    BLOB_ID_PATTERN,
    BlobKind,
    BlobNotFoundError,
    BlobRef,
    BlobStore,
)

EXPIRES_AT = datetime.now(UTC) + timedelta(days=30)


def put(store: BlobStore, data: bytes, kind: BlobKind = BlobKind.AUDIO) -> BlobRef:
    content_type = "audio/ogg" if kind is BlobKind.AUDIO else "image/png"
    return asyncio.run(
        store.put(data, kind=kind, content_type=content_type, expires_at=EXPIRES_AT)
    )


def test_put_then_get_returns_the_same_bytes(store: BlobStore) -> None:
    data = bytes(range(256)) * 1200
    ref = put(store, data)
    assert asyncio.run(store.get(ref.blob_id)) == data


@pytest.mark.parametrize("kind", list(BlobKind))
def test_ref_keeps_kind_content_type_size_and_expiry(
    store: BlobStore, kind: BlobKind
) -> None:
    ref = put(store, b"abc", kind)
    assert (ref.kind, ref.size, ref.expires_at) == (kind, 3, EXPIRES_AT)
    assert ref.content_type in {"audio/ogg", "image/png"}


def test_ids_are_random_and_carry_no_content(store: BlobStore) -> None:
    first, second = put(store, b"jan.kowalski@example.com"), put(store, b"x")
    assert first.blob_id != second.blob_id
    assert re.fullmatch(BLOB_ID_PATTERN, first.blob_id)
    assert first.blob_id.startswith(f"{BlobKind.AUDIO}_")
    assert "kowalski" not in first.blob_id


def test_get_after_delete_raises_not_found(store: BlobStore) -> None:
    ref = put(store, b"abc")
    asyncio.run(store.delete(ref.blob_id))
    with pytest.raises(BlobNotFoundError):
        asyncio.run(store.get(ref.blob_id))


def test_delete_of_a_missing_blob_is_a_no_op(store: BlobStore) -> None:
    asyncio.run(store.delete(f"{BlobKind.AUDIO}_{'0' * 32}"))


def test_unknown_id_raises_not_found_on_get_and_uri(store: BlobStore) -> None:
    with pytest.raises(BlobNotFoundError):
        asyncio.run(store.get(f"{BlobKind.IMAGE}_{'0' * 32}"))
    with pytest.raises(BlobNotFoundError):
        asyncio.run(store.uri(f"{BlobKind.IMAGE}_{'0' * 32}"))


@pytest.mark.parametrize("blob_id", ["", "../etc/passwd", "audio_x/../../y", "a" * 81])
def test_malformed_id_raises_not_found(store: BlobStore, blob_id: str) -> None:
    with pytest.raises(BlobNotFoundError):
        asyncio.run(store.get(blob_id))


def test_uri_names_the_blob_for_providers_that_read_from_storage(
    store: BlobStore,
) -> None:
    ref = put(store, b"abc")
    assert asyncio.run(store.uri(ref.blob_id)).endswith(ref.blob_id)


def test_ref_rejects_a_naive_expiry() -> None:
    with pytest.raises(ValueError, match="timezone"):
        BlobRef(
            blob_id=f"{BlobKind.AUDIO}_{'0' * 32}",
            kind=BlobKind.AUDIO,
            content_type="audio/ogg",
            size=1,
            expires_at=datetime(2026, 12, 1),  # ruff: ignore[call-datetime-without-tzinfo]  # naive on purpose
        )
