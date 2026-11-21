"""Job contract between meritum-backend (enqueues) and meritum-worker (runs).

The workflow specs and their versions are the contract itself, so they stay
here next to the models they are built from (see ``constants-exceptions`` in
pyproject.toml).
"""

from dataclasses import dataclass
from typing import Any, Final

from pydantic import BaseModel, Field

CONTRACT_VERSION: Final = 1
"""Version of the job contract; raise it on any change a consumer cannot read."""

APPLICATION_NAME: Final = "meritum-worker"
"""DBOS application name; the worker launches with it, the backend enqueues to it."""

DEFAULT_QUEUE: Final = "default"
"""Queue of the workflows that need no dedicated concurrency limits."""


class PingInput(BaseModel):
    """Input of the `ping` smoke-test workflow.

    Attributes:
        contract_version: the job contract version the sender speaks.
        message: text the worker echoes back.

    Features:
        ADR-03
    """

    contract_version: int = CONTRACT_VERSION
    message: str = Field(default="ping", max_length=200)


class PingOutput(BaseModel):
    """Output of the `ping` workflow: the echoed message and the worker's env.

    Attributes:
        contract_version: the job contract version of the worker.
        message: the echoed text.
        worker_env: the environment name of the worker that ran the job.

    Features:
        ADR-03
    """

    contract_version: int = CONTRACT_VERSION
    message: str
    worker_env: str


@dataclass(frozen=True, slots=True)
class WorkflowSpec[In: BaseModel, Out: BaseModel]:
    """Name, queue and payload models of one DBOS workflow.

    Attributes:
        name: the registered DBOS workflow name.
        queue: the queue the backend enqueues to.
        input: the model of the single JSON argument.
        output: the model of the JSON result.

    Features:
        ADR-03
    """

    name: str
    queue: str
    input: type[In]
    output: type[Out]


PING: Final = WorkflowSpec("ping", DEFAULT_QUEUE, PingInput, PingOutput)
"""Smoke-test workflow the deploy runs to prove the backend reaches the worker."""

WORKFLOWS: Final[tuple[WorkflowSpec[Any, Any], ...]] = (PING,)
"""Every workflow of the contract (names must be unique)."""
