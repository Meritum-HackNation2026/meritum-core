"""Ports of the jobs slice."""

from collections.abc import AsyncIterator
from typing import Any, Protocol

from pydantic import BaseModel

from meritum_core.jobs.constants import EVENT_TIMEOUT_SECONDS
from meritum_core.jobs.contracts import WorkflowSpec


class JobState(BaseModel):
    """What the caller may see about one job.

    Attributes:
        workflow_id: the DBOS workflow id.
        status: the DBOS workflow status (ENQUEUED, PENDING, SUCCESS, ERROR,
            CANCELLED, ...).
        output: the workflow result as JSON, once it succeeded.
        error: the error text, once it failed.

    Features:
        ADR-03
    """

    workflow_id: str
    status: str
    output: dict[str, Any] | None = None
    error: str | None = None


class JobQueue(Protocol):
    """Enqueues workflows on the worker and reads their state and output (port).

    Workflows publish values as JSON objects (`model_dump(mode="json")`):
    a stream is an ordered sequence under one key (`PROGRESS_KEY`), an event is
    the latest value under one key (`READINESS_KEY`).

    Features:
        ADR-01, ADR-03, F-09, US-WDR-08
    """

    async def enqueue[In: BaseModel](
        self,
        spec: WorkflowSpec[In, Any],
        payload: In,
        *,
        workflow_id: str | None = None,
    ) -> str:
        """Enqueue `spec` with `payload` and return the workflow id.

        Args:
            spec: the workflow to run.
            payload: its input model.
            workflow_id: an idempotency key; generated when None.
        """
        ...

    async def state(self, workflow_id: str) -> JobState | None:
        """Return the job's state, or None when no such workflow exists.

        Args:
            workflow_id: the id `enqueue` returned.
        """
        ...

    def stream[T: BaseModel](
        self, workflow_id: str, key: str, model: type[T]
    ) -> AsyncIterator[T]:
        """Yield the values a workflow writes to stream `key`, in order.

        Ends when the workflow closes the stream or terminates.

        Args:
            workflow_id: the id `enqueue` returned.
            key: the stream key, e.g. `PROGRESS_KEY`.
            model: the model every value validates against.
        """
        ...

    async def event[T: BaseModel](
        self,
        workflow_id: str,
        key: str,
        model: type[T],
        *,
        timeout_seconds: float = EVENT_TIMEOUT_SECONDS,
    ) -> T | None:
        """Return the latest value of event `key`, or None if none came in time.

        Args:
            workflow_id: the id `enqueue` returned.
            key: the event key, e.g. `READINESS_KEY`.
            model: the model the value validates against.
            timeout_seconds: how long to wait for a value.
        """
        ...
