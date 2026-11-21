"""The repositories the Notification contract runs on; core/038 adds PostgreSQL here."""

import asyncio
from collections.abc import Callable, Iterator

import pytest

from meritum_core.notifications import NotificationRepository
from meritum_core.notifications.fakes import InMemoryNotificationRepository

ADAPTERS: dict[str, Callable[[], NotificationRepository]] = {
    "memory": InMemoryNotificationRepository,
}


@pytest.fixture(params=sorted(ADAPTERS))
def notes(request: pytest.FixtureRequest) -> NotificationRepository:
    assert isinstance(request.param, str)
    return ADAPTERS[request.param]()


@pytest.fixture
def run() -> Iterator[asyncio.Runner]:
    """One event loop per test, so adapters with loop-bound pools work."""
    with asyncio.Runner() as runner:
        yield runner
