"""The adapters the BlobStore contract runs on; core/021 and core/022 add theirs here.

Each entry builds the settings of one adapter; ``tmp_path`` is there for adapters
that need a directory (filesystem) or a local emulator's state.
"""

import asyncio
from collections.abc import Callable, Iterator
from pathlib import Path

import pytest

from meritum_core.shared.blobs import (
    BlobProvider,
    BlobSettings,
    BlobStore,
    build_blob_store,
)


def _memory(_: Path) -> BlobSettings:
    return BlobSettings(provider=BlobProvider.MEMORY)


ADAPTERS: dict[str, Callable[[Path], BlobSettings]] = {"memory": _memory}


@pytest.fixture(params=sorted(ADAPTERS))
def store(request: pytest.FixtureRequest, tmp_path: Path) -> BlobStore:
    assert isinstance(request.param, str)
    return build_blob_store(ADAPTERS[request.param](tmp_path))


@pytest.fixture
def run() -> Iterator[asyncio.Runner]:
    """One event loop per test, so adapters with loop-bound clients work."""
    with asyncio.Runner() as runner:
        yield runner
