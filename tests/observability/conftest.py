"""App repositories the SubjectEraser contract runs on: the fakes and PostgreSQL.

PostgreSQL runs only with ``uv run pytest -m integration``.
"""

import asyncio
from collections.abc import Iterator

import pytest

from meritum_core.observability import AppRepositories, build_app_repositories
from meritum_core.shared.database import DatabaseProvider, DatabaseSettings


@pytest.fixture(
    params=["memory", pytest.param("postgres", marks=pytest.mark.integration)]
)
def app(request: pytest.FixtureRequest) -> AppRepositories:
    if request.param == "memory":
        return build_app_repositories(DatabaseSettings())
    url = request.getfixturevalue("app_database_url")
    settings = DatabaseSettings(provider=DatabaseProvider.POSTGRES, url=url)
    return build_app_repositories(settings)


@pytest.fixture
def run() -> Iterator[asyncio.Runner]:
    """One event loop per test, so adapters with loop-bound pools work."""
    with asyncio.Runner() as runner:
        yield runner
