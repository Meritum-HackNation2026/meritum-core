"""Ports of the jobs slice."""

from typing import Any, Protocol

from pydantic import BaseModel

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
    """Enqueues workflows on the worker and reads their state (port).

    Features:
        ADR-01, ADR-03
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
