"""The adapters the BlobStore contract runs on; core/021, core/022 and core/037 add theirs here.

Each entry builds the settings of one adapter; ``tmp_path`` is there for adapters
that need a directory (filesystem) or a local emulator's state. GCS and S3 run on
in-process fakes on localhost, never on a real bucket.
"""

import asyncio
import socket
from collections.abc import Callable, Iterator
from pathlib import Path

import boto3
import pytest
from gcp_storage_emulator.server import create_server
from moto.server import ThreadedMotoServer

from meritum_core.shared.blobs import (
    BlobProvider,
    BlobSettings,
    BlobStore,
    build_blob_store,
)

GCS_TEST_BUCKET = "meritum-test-blobs"
S3_TEST_BUCKET = "meritum-test-s3"
S3_TEST_REGION = "eu-central-1"


def _memory(_: Path, __: str) -> BlobSettings:
    return BlobSettings(provider=BlobProvider.MEMORY)


def _filesystem(tmp_path: Path, _: str) -> BlobSettings:
    return BlobSettings(provider=BlobProvider.FILESYSTEM, directory=tmp_path / "blobs")


def _gcs(_: Path, __: str) -> BlobSettings:
    return BlobSettings(provider=BlobProvider.GCS, bucket=GCS_TEST_BUCKET)


def _s3(_: Path, endpoint: str) -> BlobSettings:
    return BlobSettings(
        provider=BlobProvider.S3,
        bucket=S3_TEST_BUCKET,
        endpoint_url=endpoint,
        region=S3_TEST_REGION,
    )


ADAPTERS: dict[str, Callable[[Path, str], BlobSettings]] = {
    "memory": _memory,
    "filesystem": _filesystem,
    "gcs": _gcs,
    "s3": _s3,
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


@pytest.fixture(scope="session")
def s3_server() -> Iterator[str]:
    """In-process S3 server (moto) on a free localhost port; yields its address."""
    server = ThreadedMotoServer(ip_address="127.0.0.1", port=0, verbose=False)
    server.start()
    host, port = server.get_host_and_port()
    endpoint = f"http://{host}:{port}"
    boto3.client(
        "s3",
        endpoint_url=endpoint,
        region_name=S3_TEST_REGION,
        aws_access_key_id="test",
        aws_secret_access_key="test",  # ruff: ignore[hardcoded-password-func-arg] - a throwaway fake
    ).create_bucket(
        Bucket=S3_TEST_BUCKET,
        CreateBucketConfiguration={"LocationConstraint": S3_TEST_REGION},
    )
    yield endpoint
    server.stop()


@pytest.fixture(params=sorted(ADAPTERS))
def store(
    request: pytest.FixtureRequest,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    gcs_emulator: str,
    s3_server: str,
) -> BlobStore:
    assert isinstance(request.param, str)
    monkeypatch.setenv("STORAGE_EMULATOR_HOST", gcs_emulator)  # the GCS client reads it
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "test")  # keys only from the environment
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "test")
    return build_blob_store(ADAPTERS[request.param](tmp_path, s3_server))


@pytest.fixture
def run() -> Iterator[asyncio.Runner]:
    """One event loop per test, so adapters with loop-bound clients work."""
    with asyncio.Runner() as runner:
        yield runner
