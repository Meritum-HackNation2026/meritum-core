"""The adapters the BlobStore contract runs on; core/021 and core/022 add theirs here."""

import pytest

from meritum_core.shared.blobs import (
    BlobProvider,
    BlobSettings,
    BlobStore,
    build_blob_store,
)


@pytest.fixture(params=[BlobProvider.MEMORY])
def store(request: pytest.FixtureRequest) -> BlobStore:
    assert isinstance(request.param, BlobProvider)
    return build_blob_store(BlobSettings(provider=request.param))
