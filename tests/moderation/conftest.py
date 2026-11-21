"""The repositories the moderation contracts run on: the fakes and PostgreSQL.

PostgreSQL runs only with ``uv run pytest -m integration`` (``app_database_url``
in tests/conftest.py gives each test its own migrated schema).
"""

import asyncio
from collections.abc import Iterator

import pytest

from meritum_core.moderation import HighRiskTopicRepository, ModeratorCaseRepository
from meritum_core.moderation.fakes import (
    InMemoryHighRiskTopicRepository,
    InMemoryModeratorCaseRepository,
)
from meritum_core.observability import AppRepositories, build_app_repositories
from meritum_core.shared.database import DatabaseProvider, DatabaseSettings

ADAPTERS = ["memory", pytest.param("postgres", marks=pytest.mark.integration)]


def _postgres(request: pytest.FixtureRequest) -> AppRepositories:
    url = request.getfixturevalue("app_database_url")
    settings = DatabaseSettings(provider=DatabaseProvider.POSTGRES, url=url)
    return build_app_repositories(settings)


@pytest.fixture(params=ADAPTERS)
def cases(request: pytest.FixtureRequest) -> ModeratorCaseRepository:
    if request.param == "memory":
        return InMemoryModeratorCaseRepository()
    return _postgres(request).cases


@pytest.fixture(params=ADAPTERS)
def topics(request: pytest.FixtureRequest) -> HighRiskTopicRepository:
    if request.param == "memory":
        return InMemoryHighRiskTopicRepository()
    return _postgres(request).topics


@pytest.fixture
def run() -> Iterator[asyncio.Runner]:
    """One event loop per test, so adapters with loop-bound pools work."""
    with asyncio.Runner() as runner:
        yield runner
