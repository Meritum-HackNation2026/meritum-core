"""In-memory JobQueue for the tests of meritum-backend and meritum-worker.

Features:
    ADR-03, F-09
"""

from collections import defaultdict
from collections.abc import AsyncIterator
from typing import Any, NamedTuple
from uuid import uuid4

from pydantic import BaseModel, JsonValue

from meritum_core.jobs.constants import EVENT_TIMEOUT_SECONDS
from meritum_core.jobs.contracts import WorkflowSpec
from meritum_core.jobs.ports import JobState

type _Json = dict[str, JsonValue]


class EnqueuedJob(NamedTuple):
    """One job the fake recorded.

    Attributes:
        spec: the workflow.
        payload: its input, after a JSON round trip.
        workflow_id: the id the job got.

    Features:
        ADR-03
    """

    spec: WorkflowSpec[Any, Any]
    payload: BaseModel
    workflow_id: str


class InMemoryJobQueue:
    """JobQueue that records enqueued jobs and replays published values.

    Payloads and values go through JSON, like DBOS keeps them, so a model that
    does not survive the round trip fails here too. A stream yields what was
    published before it is read and then ends, as a finished workflow's would.

    Attributes:
        enqueued: every enqueued job, in order; a repeated workflow id is one job.

    Features:
        ADR-03, F-09
    """

    def __init__(self) -> None:
        self.enqueued: list[EnqueuedJob] = []
        self._streams: defaultdict[tuple[str, str], list[_Json]] = defaultdict(list)
        self._events: dict[tuple[str, str], _Json] = {}

    async def enqueue[In: BaseModel](
        self,
        spec: WorkflowSpec[In, Any],
        payload: In,
        *,
        workflow_id: str | None = None,
    ) -> str:
        """Record the job once per workflow id, like DBOS.

        Args:
            spec: the workflow to run.
            payload: its input model.
            workflow_id: an idempotency key; a random one when None.

        Returns:
            The workflow id.

        Raises:
            TypeError: `payload` is not the input model of `spec`.
        """
        if not isinstance(payload, spec.input):
            msg = f"{spec.name} takes {spec.input.__name__}"
            raise TypeError(msg)
        workflow_id = workflow_id or uuid4().hex
        if not self._known(workflow_id):
            sent = spec.input.model_validate(payload.model_dump(mode="json"))
            self.enqueued.append(EnqueuedJob(spec, sent, workflow_id))
        return workflow_id

    def _known(self, workflow_id: str) -> bool:
        return any(job.workflow_id == workflow_id for job in self.enqueued)

    async def state(self, workflow_id: str) -> JobState | None:
        """Report an enqueued job as ENQUEUED.

        Args:
            workflow_id: the id `enqueue` returned.

        Returns:
            The state, or None for an unknown id.
        """
        if not self._known(workflow_id):
            return None
        return JobState(workflow_id=workflow_id, status="ENQUEUED")

    def publish(self, workflow_id: str, key: str, value: BaseModel) -> None:
        """Append `value` to stream `key`, as a workflow would.

        Args:
            workflow_id: the workflow that writes.
            key: the stream key.
            value: the value to append.
        """
        self._streams[workflow_id, key].append(value.model_dump(mode="json"))

    def set_event(self, workflow_id: str, key: str, value: BaseModel) -> None:
        """Set event `key` to `value`, as a workflow would.

        Args:
            workflow_id: the workflow that sets it.
            key: the event key.
            value: the new value.
        """
        self._events[workflow_id, key] = value.model_dump(mode="json")

    async def stream[T: BaseModel](
        self, workflow_id: str, key: str, model: type[T]
    ) -> AsyncIterator[T]:
        """Yield every value published so far to stream `key`, in order.

        A value that does not match `model` raises pydantic's ValidationError.

        Args:
            workflow_id: the workflow that wrote the stream.
            key: the stream key.
            model: the model every value validates against.

        Yields:
            The published values.
        """
        for value in self._streams.get((workflow_id, key), []):
            yield model.model_validate(value)

    async def event[T: BaseModel](
        self,
        workflow_id: str,
        key: str,
        model: type[T],
        *,
        timeout_seconds: float = EVENT_TIMEOUT_SECONDS,  # ruff: ignore[unused-method-argument]  # matches the port; the fake never waits
    ) -> T | None:
        """Return the event's value, or None when it was never set.

        A value that does not match `model` raises pydantic's ValidationError.

        Args:
            workflow_id: the workflow that set it.
            key: the event key.
            model: the model the value validates against.
            timeout_seconds: ignored; the fake answers at once.

        Returns:
            The value or None.
        """
        value = self._events.get((workflow_id, key))
        return None if value is None else model.model_validate(value)
