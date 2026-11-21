"""The repositories the moderation contracts run on; core/038 adds PostgreSQL here."""

import asyncio
from collections.abc import Callable, Iterator

import pytest

from meritum_core.moderation import (
    HighRiskTopicRepository,
    InMemoryHighRiskTopicRepository,
    InMemoryModeratorCaseRepository,
    ModeratorCaseRepository,
)

CASE_ADAPTERS: dict[str, Callable[[], ModeratorCaseRepository]] = {
    "memory": InMemoryModeratorCaseRepository,
}
TOPIC_ADAPTERS: dict[str, Callable[[], HighRiskTopicRepository]] = {
    "memory": InMemoryHighRiskTopicRepository,
}


@pytest.fixture(params=sorted(CASE_ADAPTERS))
def cases(request: pytest.FixtureRequest) -> ModeratorCaseRepository:
    assert isinstance(request.param, str)
    return CASE_ADAPTERS[request.param]()


@pytest.fixture(params=sorted(TOPIC_ADAPTERS))
def topics(request: pytest.FixtureRequest) -> HighRiskTopicRepository:
    assert isinstance(request.param, str)
    return TOPIC_ADAPTERS[request.param]()


@pytest.fixture
def run() -> Iterator[asyncio.Runner]:
    """One event loop per test, so adapters with loop-bound pools work."""
    with asyncio.Runner() as runner:
        yield runner
