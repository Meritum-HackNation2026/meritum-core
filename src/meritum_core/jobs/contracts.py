"""Job contract between meritum-backend (enqueues) and meritum-worker (runs)."""

from dataclasses import dataclass
from typing import Any

from pydantic import BaseModel, Field

CONTRACT_VERSION = 1
# DBOS application name; the worker launches with it, the backend enqueues to it.
APPLICATION_NAME = "meritum-worker"
DEFAULT_QUEUE = "default"


class PingInput(BaseModel):
    """Input of the `ping` smoke-test workflow."""

    contract_version: int = CONTRACT_VERSION
    message: str = Field(default="ping", max_length=200)


class PingOutput(BaseModel):
    """Output of the `ping` workflow: the echoed message and the worker's env."""

    contract_version: int = CONTRACT_VERSION
    message: str
    worker_env: str


@dataclass(frozen=True, slots=True)
class WorkflowSpec[In: BaseModel, Out: BaseModel]:
    """Name, queue and payload models of one DBOS workflow."""

    name: str
    queue: str
    input: type[In]
    output: type[Out]


PING = WorkflowSpec("ping", DEFAULT_QUEUE, PingInput, PingOutput)

WORKFLOWS: tuple[WorkflowSpec[Any, Any], ...] = (PING,)
