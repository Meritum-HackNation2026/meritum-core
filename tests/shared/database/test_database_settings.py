"""DatabaseSettings and the app repository factory, without a database."""

import pytest
from pydantic import ValidationError

from meritum_core.checks.fakes import InMemoryCheckRecordRepository
from meritum_core.observability import build_app_repositories
from meritum_core.shared.database import DatabaseProvider, DatabaseSettings


def test_memory_is_the_default_and_builds_the_fakes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("MERITUM_DATABASE_PROVIDER", raising=False)
    settings = DatabaseSettings()
    assert settings.provider is DatabaseProvider.MEMORY
    assert isinstance(
        build_app_repositories(settings).records, InMemoryCheckRecordRepository
    )


def test_postgres_reads_the_url_from_the_environment(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("MERITUM_DATABASE_PROVIDER", "postgres")
    monkeypatch.setenv("MERITUM_DATABASE_URL", "postgresql://u@h/meritum")
    settings = DatabaseSettings()
    assert settings.url is not None
    assert settings.url.get_secret_value() == "postgresql://u@h/meritum"


def test_postgres_without_a_url_is_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("MERITUM_DATABASE_URL", raising=False)
    with pytest.raises(ValidationError, match="MERITUM_DATABASE_URL"):
        DatabaseSettings(provider=DatabaseProvider.POSTGRES)


def test_postgres_factory_needs_a_url() -> None:
    unchecked = DatabaseSettings.model_construct(provider=DatabaseProvider.POSTGRES)
    with pytest.raises(ValueError, match="MERITUM_DATABASE_URL"):
        build_app_repositories(unchecked)
