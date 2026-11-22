"""build_blob_store picks the adapter from MERITUM_BLOB_* variables."""

import pytest
from pydantic import ValidationError

from meritum_core.shared.blobs import (
    BlobError,
    BlobProvider,
    BlobSettings,
    build_blob_store,
)


def test_provider_comes_from_the_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MERITUM_BLOB_PROVIDER", "memory")
    settings = BlobSettings()
    assert settings.provider is BlobProvider.MEMORY
    assert build_blob_store(settings) is not build_blob_store(settings)


def test_missing_provider_fails_loudly(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("MERITUM_BLOB_PROVIDER", raising=False)
    with pytest.raises(ValidationError, match="provider"):
        BlobSettings()


@pytest.mark.parametrize(
    ("provider", "variable"),
    [
        (BlobProvider.FILESYSTEM, "MERITUM_BLOB_DIRECTORY"),
        (BlobProvider.GCS, "MERITUM_BLOB_BUCKET"),
    ],
)
def test_provider_without_its_location_fails_loudly(
    monkeypatch: pytest.MonkeyPatch, provider: BlobProvider, variable: str
) -> None:
    monkeypatch.setenv("MERITUM_BLOB_PROVIDER", provider)
    monkeypatch.delenv(variable, raising=False)
    with pytest.raises(BlobError, match=variable):
        build_blob_store(BlobSettings())


def test_s3_without_a_bucket_fails_loudly(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MERITUM_BLOB_PROVIDER", "s3")
    monkeypatch.delenv("MERITUM_BLOB_BUCKET", raising=False)
    with pytest.raises(BlobError, match="MERITUM_BLOB_BUCKET"):
        build_blob_store(BlobSettings())
