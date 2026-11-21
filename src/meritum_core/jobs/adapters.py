"""DBOS implementation of the JobQueue port."""

from typing import Any

from dbos import DBOSClient, EnqueueOptions, WorkflowSerializationFormat
from pydantic import BaseModel

from meritum_core.jobs.contracts import APPLICATION_NAME, WorkflowSpec
from meritum_core.jobs.ports import JobState


class DbosJobQueue:
    """JobQueue over `DBOSClient` (the backend never runs workflows itself).

    Args:
        client: client bound to the worker's system database and schema.
        app_version: the environment name; the worker only dequeues its own.

    Features:
        ADR-03
    """

    def __init__(self, client: DBOSClient, app_version: str) -> None:
        self._client = client
        self._app_version = app_version

    async def enqueue[In: BaseModel](
        self,
        spec: WorkflowSpec[In, Any],
        payload: In,
        *,
        workflow_id: str | None = None,
    ) -> str:
        """Enqueue `spec` with one portable JSON argument.

        Args:
            spec: the workflow to run.
            payload: its input model, sent as a JSON object.
            workflow_id: an idempotency key; DBOS generates one when None.

        Returns:
            The workflow id (the given one, or a generated one).
        """
        options: EnqueueOptions = {
            "workflow_name": spec.name,
            "queue_name": spec.queue,
            "app_version": self._app_version,
            "application_name": APPLICATION_NAME,
            "serialization_type": WorkflowSerializationFormat.PORTABLE,
        }
        if workflow_id is not None:
            options["workflow_id"] = workflow_id
        handle = await self._client.enqueue_async(
            options, payload.model_dump(mode="json")
        )
        return handle.get_workflow_id()

    async def state(self, workflow_id: str) -> JobState | None:
        """Read the workflow status.

        Args:
            workflow_id: the id `enqueue` returned.

        Returns:
            The state, or None when DBOS does not know the id.
        """
        found = await self._client.list_workflows_async(workflow_ids=[workflow_id])
        if not found:
            return None
        status = found[0]
        return JobState(
            workflow_id=workflow_id,
            status=str(status.status),
            output=status.output if isinstance(status.output, dict) else None,
            error=None if status.error is None else str(status.error),
        )
