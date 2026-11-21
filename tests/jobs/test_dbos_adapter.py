import asyncio
from collections.abc import AsyncIterator
from typing import cast

from dbos import DBOSClient

from meritum_core.checks import AnalysisStatus, AnalysisStep
from meritum_core.jobs.adapters import DbosJobQueue
from meritum_core.jobs.constants import PROGRESS_KEY, READINESS_KEY
from meritum_core.jobs.contracts import ReadinessReport

STATUSES = [
    AnalysisStatus(check_id="c1", steps=[AnalysisStep(code="receive", status=s)])
    for s in ("pending", "active", "done")
]
REPORT = ReadinessReport(
    missing_env=["X"], unavailable_providers=[], checked_at="2026-11-21T00:00:00Z"
)


class _Client:
    """Stands in for DBOSClient: returns JSON like a portable workflow wrote it."""

    def __init__(self) -> None:
        self.calls: list[tuple[str, ...]] = []

    async def read_stream_async(
        self, workflow_id: str, key: str
    ) -> AsyncIterator[object]:
        self.calls.append(("stream", workflow_id, key))
        for status in STATUSES:
            yield status.model_dump(mode="json")

    async def get_event_async(
        self, workflow_id: str, key: str, timeout_seconds: float
    ) -> object:
        self.calls.append(("event", workflow_id, key, str(timeout_seconds)))
        return REPORT.model_dump(mode="json") if key == READINESS_KEY else None


def _queue() -> tuple[DbosJobQueue, _Client]:
    client = _Client()
    return DbosJobQueue(cast("DBOSClient", client), "local"), client


def test_stream_validates_dbos_values_in_order() -> None:
    queue, client = _queue()

    async def read() -> list[AnalysisStatus]:
        return [s async for s in queue.stream("w1", PROGRESS_KEY, AnalysisStatus)]

    assert asyncio.run(read()) == STATUSES
    assert client.calls == [("stream", "w1", PROGRESS_KEY)]


def test_event_validates_the_value_or_returns_none() -> None:
    queue, client = _queue()
    got = asyncio.run(queue.event("w1", READINESS_KEY, ReadinessReport))
    assert got == REPORT
    missing = asyncio.run(
        queue.event("w1", "other", ReadinessReport, timeout_seconds=0.1)
    )
    assert missing is None
    assert client.calls[-1] == ("event", "w1", "other", "0.1")
