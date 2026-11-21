"""Steps for the filesystem and GCS scenarios of features/blobs.feature.

GCS runs on an in-process emulator on localhost, so no network and no bucket.
"""

import asyncio
import os
import socket
from datetime import UTC, datetime, timedelta
from pathlib import Path
from tempfile import TemporaryDirectory

from behave import given, then, when
from behave.runner import Context
from gcp_storage_emulator.server import create_server

from meritum_core.shared.blobs import (
    BlobKind,
    BlobNotFoundError,
    BlobProvider,
    BlobRef,
    BlobSettings,
    BlobStore,
    build_blob_store,
)


def _put(store: BlobStore, data: bytes) -> BlobRef:
    expires_at = datetime.now(UTC) + timedelta(days=30)
    return asyncio.run(
        store.put(
            data, kind=BlobKind.AUDIO, content_type="audio/ogg", expires_at=expires_at
        )
    )


def _start_gcs_emulator(context: Context, bucket: str) -> None:
    with socket.socket() as probe:
        probe.bind(("localhost", 0))
        port = probe.getsockname()[1]
    server = create_server("localhost", port, in_memory=True, default_bucket=bucket)
    server.start()
    context.add_cleanup(server.stop)
    previous = os.environ.get("STORAGE_EMULATOR_HOST")
    os.environ["STORAGE_EMULATOR_HOST"] = f"http://localhost:{port}"
    if previous is None:
        context.add_cleanup(os.environ.pop, "STORAGE_EMULATOR_HOST")
    else:
        context.add_cleanup(os.environ.__setitem__, "STORAGE_EMULATOR_HOST", previous)


@given("MERITUM_BLOB_PROVIDER=filesystem i katalog wolumenu")
def given_filesystem_volume(context: Context) -> None:
    """A shared volume directory both processes mount."""
    volume = TemporaryDirectory()
    context.add_cleanup(volume.cleanup)
    context.directory = Path(volume.name)
    context.settings = BlobSettings(
        provider=BlobProvider.FILESYSTEM, directory=context.directory
    )


@when("backend zapisuje nagranie, a worker je odczytuje")
def when_backend_saves_and_worker_reads(context: Context) -> None:
    """Backend and worker each build their own store from the same settings."""
    backend, worker = (
        build_blob_store(context.settings),
        build_blob_store(context.settings),
    )
    context.data = b"OggS" + bytes(4096)
    context.ref = _put(backend, context.data)
    context.read = asyncio.run(worker.get(context.ref.blob_id))
    context.worker = worker


@then("oba procesy widzą ten sam plik, a usunięcie kasuje go z dysku")
def then_same_file_and_delete_removes_it(context: Context) -> None:
    """The worker reads the backend's bytes; delete leaves no file in the volume."""
    assert context.read == context.data
    assert (context.directory / context.ref.blob_id).is_file()
    asyncio.run(context.worker.delete(context.ref.blob_id))
    assert list(context.directory.iterdir()) == []


@given("MERITUM_BLOB_PROVIDER=gcs i nazwa bucketu")
def given_gcs_bucket(context: Context) -> None:
    """A bucket on the in-process emulator."""
    context.bucket = "meritum-recordings"
    _start_gcs_emulator(context, context.bucket)
    context.settings = BlobSettings(provider=BlobProvider.GCS, bucket=context.bucket)


@when("worker prosi o adres nagrania dłuższego niż około minuty")
def when_worker_asks_for_uri(context: Context) -> None:
    """Store a long recording and ask for its provider address."""
    store = build_blob_store(context.settings)
    context.ref = _put(store, b"OggS" + bytes(2 * 1024 * 1024))
    context.uri = asyncio.run(store.uri(context.ref.blob_id))
    context.store = store


@then("dostaje adres gs:// do odczytu przez Speech-to-Text w trybie batch")
def then_gets_gs_uri(context: Context) -> None:
    """The address names the bucket and the blob; a deleted blob has none."""
    assert context.uri == f"gs://{context.bucket}/{context.ref.blob_id}"
    asyncio.run(context.store.delete(context.ref.blob_id))
    try:
        asyncio.run(context.store.uri(context.ref.blob_id))
        has_uri = True
    except BlobNotFoundError:
        has_uri = False
    assert not has_uri
