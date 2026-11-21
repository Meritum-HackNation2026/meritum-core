"""The adapters the BlobStore contract runs on; core/021 and core/022 add theirs here.

Each entry builds the settings of one adapter; ``tmp_path`` is there for adapters
that need a directory (filesystem) or a local emulator's state. GCS runs on an
in-process emulator on localhost, never on a real bucket.
"""

import asyncio
import socket
from collections.abc import Callable, Iterator
from pathlib import Path

import pytest
from gcp_storage_emulator.server import create_server

from meritum_core.shared.blobs import (
    BlobProvider,
    BlobSettings,
    BlobStore,
    build_blob_store,
)

GCS_TEST_BUCKET = "meritum-test-blobs"


def _memory(_: Path) -> BlobSettings:
    return BlobSettings(provider=BlobProvider.MEMORY)


def _filesystem(tmp_path: Path) -> BlobSettings:
    return BlobSettings(provider=BlobProvider.FILESYSTEM, directory=tmp_path / "blobs")


def _gcs(_: Path) -> BlobSettings:
    return BlobSettings(provider=BlobProvider.GCS, bucket=GCS_TEST_BUCKET)


ADAPTERS: dict[str, Callable[[Path], BlobSettings]] = {
    "memory": _memory,
    "filesystem": _filesystem,
    "gcs": _gcs,
}


@pytest.fixture(scope="session")
def gcs_emulator() -> Iterator[str]:
    """In-process GCS emulator on a free localhost port; yields its address."""
    with socket.socket() as probe:
        probe.bind(("localhost", 0))
        port = probe.getsockname()[1]
    server = create_server(
        "localhost", port, in_memory=True, default_bucket=GCS_TEST_BUCKET
    )
    server.start()
    yield f"http://localhost:{port}"
    server.stop()


@pytest.fixture(params=sorted(ADAPTERS))
def store(
    request: pytest.FixtureRequest,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    gcs_emulator: str,
) -> BlobStore:
    assert isinstance(request.param, str)
    monkeypatch.setenv("STORAGE_EMULATOR_HOST", gcs_emulator)  # the GCS client reads it
    return build_blob_store(ADAPTERS[request.param](tmp_path))


@pytest.fixture
def run() -> Iterator[asyncio.Runner]:
    """One event loop per test, so adapters with loop-bound clients work."""
    with asyncio.Runner() as runner:
        yield runner
