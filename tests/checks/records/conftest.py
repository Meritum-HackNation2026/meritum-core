"""The repositories the CheckRecord contract runs on: the fake and PostgreSQL.

PostgreSQL runs only with ``uv run pytest -m integration`` (``app_database_url``
in tests/conftest.py gives each test its own migrated schema).
"""

import asyncio
from collections.abc import Iterator

import pytest

from meritum_core.checks import CheckRecordRepository
from meritum_core.checks.fakes import InMemoryCheckRecordRepository
from meritum_core.observability import build_app_repositories
from meritum_core.shared.database import DatabaseProvider, DatabaseSettings


@pytest.fixture(
    params=["memory", pytest.param("postgres", marks=pytest.mark.integration)]
)
def records(request: pytest.FixtureRequest) -> CheckRecordRepository:
    if request.param == "memory":
        return InMemoryCheckRecordRepository()
    url = request.getfixturevalue("app_database_url")
    settings = DatabaseSettings(provider=DatabaseProvider.POSTGRES, url=url)
    return build_app_repositories(settings).records


@pytest.fixture
def run() -> Iterator[asyncio.Runner]:
    """One event loop per test, so adapters with loop-bound pools work."""
    with asyncio.Runner() as runner:
        yield runner
