"""BlobStore port contract: every adapter in conftest.py must pass these tests."""

import asyncio
import re
from datetime import UTC, datetime, timedelta

import pytest
from pydantic import ValidationError

from meritum_core.shared.blobs import (
    BLOB_ID_PATTERN,
    BlobKind,
    BlobNotFoundError,
    BlobRef,
    BlobStore,
)

EXPIRES_AT = datetime.now(UTC) + timedelta(days=30)
CONTENT_TYPES = {BlobKind.AUDIO: "audio/ogg", BlobKind.IMAGE: "image/png"}
UNKNOWN_ID = f"{BlobKind.AUDIO}_{'0' * 32}"
MALFORMED_IDS = ["", "../etc/passwd", f"{BlobKind.AUDIO}_../../x", "a" * 81]


def put(
    run: asyncio.Runner, store: BlobStore, data: bytes, kind: BlobKind = BlobKind.AUDIO
) -> BlobRef:
    return run.run(
        store.put(
            data, kind=kind, content_type=CONTENT_TYPES[kind], expires_at=EXPIRES_AT
        )
    )


def test_put_then_get_returns_the_same_bytes(
    run: asyncio.Runner, store: BlobStore
) -> None:
    data = bytes(range(256)) * 1200
    ref = put(run, store, data)
    assert run.run(store.get(ref.blob_id)) == data


@pytest.mark.parametrize("kind", list(BlobKind))
def test_ref_keeps_kind_content_type_size_and_expiry(
    run: asyncio.Runner, store: BlobStore, kind: BlobKind
) -> None:
    ref = put(run, store, b"abc", kind)
    assert (ref.kind, ref.content_type, ref.size, ref.expires_at) == (
        kind,
        CONTENT_TYPES[kind],
        3,
        EXPIRES_AT,
    )


def test_ids_are_random_and_name_their_kind(
    run: asyncio.Runner, store: BlobStore
) -> None:
    first, second = put(run, store, b"x"), put(run, store, b"x")
    assert first.blob_id != second.blob_id
    assert re.fullmatch(BLOB_ID_PATTERN, first.blob_id)
    assert first.blob_id.startswith(f"{BlobKind.AUDIO}_")


def test_get_after_delete_raises_not_found(
    run: asyncio.Runner, store: BlobStore
) -> None:
    ref = put(run, store, b"abc")
    run.run(store.delete(ref.blob_id))
    with pytest.raises(BlobNotFoundError):
        run.run(store.get(ref.blob_id))
    with pytest.raises(BlobNotFoundError):
        run.run(store.uri(ref.blob_id))


def test_delete_of_a_missing_blob_is_a_no_op(
    run: asyncio.Runner, store: BlobStore
) -> None:
    run.run(store.delete(UNKNOWN_ID))


def test_unknown_id_raises_not_found(run: asyncio.Runner, store: BlobStore) -> None:
    with pytest.raises(BlobNotFoundError):
        run.run(store.get(UNKNOWN_ID))
    with pytest.raises(BlobNotFoundError):
        run.run(store.uri(UNKNOWN_ID))


@pytest.mark.parametrize("blob_id", MALFORMED_IDS)
@pytest.mark.parametrize("method", ["get", "delete", "uri"])
def test_malformed_id_raises_not_found_on_every_method(
    run: asyncio.Runner, store: BlobStore, method: str, blob_id: str
) -> None:
    call = {"get": store.get, "delete": store.delete, "uri": store.uri}[method]
    with pytest.raises(BlobNotFoundError):
        run.run(call(blob_id))


def test_uri_names_the_blob_for_providers_that_read_from_storage(
    run: asyncio.Runner, store: BlobStore
) -> None:
    ref = put(run, store, b"abc")
    assert run.run(store.uri(ref.blob_id)).endswith(ref.blob_id)


def test_naive_expiry_is_rejected(
    run: asyncio.Runner, store: BlobStore
) -> None:
    naive = EXPIRES_AT.replace(tzinfo=None)
    with pytest.raises(ValidationError, match="expires_at"):
        run.run(
            store.put(
                b"abc", kind=BlobKind.AUDIO, content_type="audio/ogg", expires_at=naive
            )
        )
