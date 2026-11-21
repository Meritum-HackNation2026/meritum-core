"""Steps for features/blobs.feature: backend and worker share one BlobStore."""

import asyncio
from datetime import UTC, datetime, timedelta

from behave import given, then, when
from behave.runner import Context

from meritum_core.shared.blobs import (
    BlobKind,
    BlobNotFoundError,
    BlobProvider,
    BlobSettings,
    BlobStore,
    build_blob_store,
)


def _store(context: Context) -> BlobStore:
    """One store per scenario, built the way backend and worker build it.

    Returns:
        The scenario's store.
    """
    if not hasattr(context, "store"):
        context.store = build_blob_store(BlobSettings(provider=BlobProvider.MEMORY))
    return context.store


def _save(context: Context, data: bytes) -> None:
    expires_at = datetime.now(UTC) + timedelta(days=30)
    context.ref = asyncio.run(
        _store(context).put(
            data, kind=BlobKind.AUDIO, content_type="audio/ogg", expires_at=expires_at
        )
    )


@given("plik OGG o rozmiarze {size:d} KB")
def given_ogg_file(context: Context, size: int) -> None:
    """Remember the bytes of an uploaded recording."""
    context.data = b"OggS" + bytes(size * 1024 - 4)


@when("backend zapisuje go przez BlobStore")
def when_backend_saves(context: Context) -> None:
    """Save the recording as the backend does after an upload."""
    _save(context, context.data)


@then("dostaje audio_id, a worker odczytuje te same bajty po tym identyfikatorze")
def then_worker_reads_same_bytes(context: Context) -> None:
    """The id names an audio blob and reads back byte for byte."""
    assert context.ref.kind is BlobKind.AUDIO
    assert asyncio.run(_store(context).get(context.ref.blob_id)) == context.data


@given("nagranie z audio_id powiązanym z session_id")
def given_recording_of_session(context: Context) -> None:
    """A stored recording; the check record links its audio_id to the session."""
    _save(context, b"OggS recording")


@when("workflow usuwania danych sesji kasuje blob")
def when_session_data_is_deleted(context: Context) -> None:
    """Delete the blob as the session data deletion workflow does."""
    asyncio.run(_store(context).delete(context.ref.blob_id))


@then("odczyt po audio_id kończy się udokumentowanym błędem „nie ma takiego pliku”")
def then_read_fails_with_not_found(context: Context) -> None:
    """Reading a deleted blob raises BlobNotFoundError."""
    try:
        asyncio.run(_store(context).get(context.ref.blob_id))
        readable = True
    except BlobNotFoundError:
        readable = False
    assert not readable
