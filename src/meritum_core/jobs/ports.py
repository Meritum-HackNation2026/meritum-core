"""Ports of the jobs slice."""

from typing import Any, Protocol

from pydantic import BaseModel

from meritum_core.jobs.contracts import WorkflowSpec


class JobState(BaseModel):
    """What the caller may see about one job."""

    workflow_id: str
    # DBOS workflow status: ENQUEUED, PENDING, SUCCESS, ERROR, CANCELLED, ...
    status: str
    output: dict[str, Any] | None = None
    error: str | None = None


class JobQueue(Protocol):
    """Enqueues workflows on the worker and reads their state."""

    async def enqueue[In: BaseModel](
        self,
        spec: WorkflowSpec[In, Any],
        payload: In,
        *,
        workflow_id: str | None = None,
    ) -> str:
        """Enqueue `spec` with `payload` and return the workflow id."""
        ...

    async def state(self, workflow_id: str) -> JobState | None:
        """Return the job's state, or None when no such workflow exists."""
        ...
