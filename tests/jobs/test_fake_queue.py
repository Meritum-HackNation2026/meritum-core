import asyncio
from collections.abc import AsyncIterator

import pytest

from meritum_core.checks import AnalysisStatus
from meritum_core.jobs.constants import PROGRESS_KEY, READINESS_KEY
from meritum_core.jobs.contracts import (
    CHECK,
    PING,
    READINESS,
    PingInput,
    ReadinessReport,
)
from meritum_core.jobs.fakes import EnqueuedJob, InMemoryJobQueue
from meritum_core.jobs.ports import JobQueue


def _status(step: str) -> AnalysisStatus:
    steps = [{"code": "receive", "status": step}]
    return AnalysisStatus.model_validate({"check_id": "c1", "steps": steps})


async def _collect(stream: AsyncIterator[AnalysisStatus]) -> list[AnalysisStatus]:
    return [item async for item in stream]


def test_fake_records_enqueued_jobs_and_reports_their_state() -> None:
    fake = InMemoryJobQueue()
    queue: JobQueue = fake
    payload = PingInput(message="hej")
    workflow_id = asyncio.run(queue.enqueue(PING, payload, workflow_id="w1"))
    assert workflow_id == "w1"
    assert fake.enqueued == [EnqueuedJob(PING, payload, "w1")]
    state = asyncio.run(queue.state("w1"))
    assert state is not None
    assert state.status == "ENQUEUED"
    assert asyncio.run(queue.state("unknown")) is None


def test_fake_treats_a_repeated_workflow_id_as_one_job() -> None:
    queue = InMemoryJobQueue()
    asyncio.run(queue.enqueue(PING, PingInput(), workflow_id="w1"))
    asyncio.run(queue.enqueue(PING, PingInput(), workflow_id="w1"))
    assert len(queue.enqueued) == 1


def test_fake_rejects_a_payload_of_another_workflow() -> None:
    queue = InMemoryJobQueue()
    with pytest.raises(TypeError):
        asyncio.run(queue.enqueue(CHECK, PingInput()))  # ty: ignore[invalid-argument-type]  # the wrong payload is the point


def test_fake_generates_distinct_ids() -> None:
    queue = InMemoryJobQueue()
    first = asyncio.run(queue.enqueue(PING, PingInput()))
    second = asyncio.run(queue.enqueue(PING, PingInput()))
    assert first != second


def test_fake_stream_keeps_publication_order_per_key() -> None:
    queue = InMemoryJobQueue()
    published = [_status("pending"), _status("active"), _status("done")]
    for status in published:
        queue.publish("w1", PROGRESS_KEY, status)
    queue.publish("w2", PROGRESS_KEY, _status("failed"))
    read = asyncio.run(_collect(queue.stream("w1", PROGRESS_KEY, AnalysisStatus)))
    assert read == published
    empty = asyncio.run(_collect(queue.stream("w1", "other", AnalysisStatus)))
    assert empty == []


def test_fake_event_returns_the_latest_value_or_none() -> None:
    queue = InMemoryJobQueue()
    assert asyncio.run(queue.event("w1", READINESS_KEY, ReadinessReport)) is None
    report = ReadinessReport(
        missing_env=[], unavailable_providers=[], checked_at="2026-11-21T00:00:00Z"
    )
    queue.set_event("w1", READINESS_KEY, report)
    got = asyncio.run(queue.event("w1", READINESS_KEY, READINESS.output))
    assert got == report
