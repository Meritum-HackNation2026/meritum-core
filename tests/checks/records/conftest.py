"""The repositories the CheckRecord contract runs on; core/038 adds PostgreSQL here."""

import asyncio
from collections.abc import Callable, Iterator

import pytest

from meritum_core.checks import CheckRecordRepository, InMemoryCheckRecordRepository

ADAPTERS: dict[str, Callable[[], CheckRecordRepository]] = {
    "memory": InMemoryCheckRecordRepository,
}


@pytest.fixture(params=sorted(ADAPTERS))
def records(request: pytest.FixtureRequest) -> CheckRecordRepository:
    assert isinstance(request.param, str)
    return ADAPTERS[request.param]()


@pytest.fixture
def run() -> Iterator[asyncio.Runner]:
    """One event loop per test, so adapters with loop-bound pools work."""
    with asyncio.Runner() as runner:
        yield runner
