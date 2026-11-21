"""build_blob_store picks the adapter from MERITUM_BLOB_* variables."""

import pytest
from pydantic import ValidationError

from meritum_core.shared.blobs import BlobProvider, BlobSettings, build_blob_store


def test_provider_comes_from_the_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MERITUM_BLOB_PROVIDER", "memory")
    settings = BlobSettings()
    assert settings.provider is BlobProvider.MEMORY
    assert build_blob_store(settings) is not build_blob_store(settings)


def test_missing_provider_fails_loudly(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("MERITUM_BLOB_PROVIDER", raising=False)
    with pytest.raises(ValidationError, match="provider"):
        BlobSettings()
