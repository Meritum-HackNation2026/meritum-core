import asyncio
from collections.abc import AsyncIterator
from datetime import UTC, datetime
from typing import cast, override

from dbos import DBOSClient

from meritum_core.checks import AnalysisStatus, AnalysisStep, CheckRequest
from meritum_core.jobs.adapters import DbosJobQueue
from meritum_core.jobs.constants import PROGRESS_KEY, READINESS_KEY
from meritum_core.jobs.contracts import CHECK, CheckInput, ReadinessReport

NOW = datetime(2026, 11, 22, tzinfo=UTC)
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


class _NewerClient(_Client):
    """A newer sender: every value carries fields this contract version lacks."""

    def __init__(self) -> None:
        super().__init__()
        self.sent: list[object] = []

    @override
    async def read_stream_async(
        self, workflow_id: str, key: str
    ) -> AsyncIterator[object]:
        async for value in super().read_stream_async(workflow_id, key):
            assert isinstance(value, dict)
            steps = [{**s, "from_v_next": 1} for s in value["steps"]]
            yield {**value, "steps": steps, "from_v_next": 1}

    @override
    async def get_event_async(
        self, workflow_id: str, key: str, timeout_seconds: float
    ) -> object:
        value = await super().get_event_async(workflow_id, key, timeout_seconds)
        return (
            None
            if value is None
            else {**cast("dict[str, object]", value), "from_v_next": 1}
        )

    async def enqueue_async(self, _options: object, payload: object) -> object:
        self.sent.append(payload)
        return type("Handle", (), {"get_workflow_id": lambda _: "w1"})()


def test_values_from_a_newer_contract_drop_unknown_fields() -> None:
    client = _NewerClient()
    queue = DbosJobQueue(cast("DBOSClient", client), "local")

    async def read() -> list[AnalysisStatus]:
        return [s async for s in queue.stream("w1", PROGRESS_KEY, AnalysisStatus)]

    assert asyncio.run(read()) == STATUSES
    assert asyncio.run(queue.event("w1", READINESS_KEY, ReadinessReport)) == REPORT


def test_enqueue_leaves_out_empty_fields_an_older_worker_may_not_know() -> None:
    client = _NewerClient()
    queue = DbosJobQueue(cast("DBOSClient", client), "local")
    request = CheckRequest(channel="web", text="Polska przyjęła euro.")
    payload = CheckInput(request=request, session_id="session-1", received_at=NOW)
    asyncio.run(queue.enqueue(CHECK, payload))
    sent = cast("dict[str, object]", client.sent[0])
    assert "image_id" not in cast("dict[str, object]", sent["request"])
    assert "user_id" not in sent
    assert CheckInput.model_validate(sent) == payload
