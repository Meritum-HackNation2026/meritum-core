"""Workflow specs: the names, queues and payload models of the job contract.

Features:
    ADR-03
"""

from dataclasses import dataclass
from typing import Any, Final

from pydantic import BaseModel

from meritum_core.jobs.constants import DEFAULT_QUEUE
from meritum_core.jobs.contracts._archive import ArchivePageInput, ArchivePageOutput
from meritum_core.jobs.contracts._check import CheckInput, CheckOutput
from meritum_core.jobs.contracts._escalation import (
    EscalateClaimInput,
    EscalateClaimOutput,
)
from meritum_core.jobs.contracts._eval_run import EvalRunInput, EvalRunOutput
from meritum_core.jobs.contracts._ping import PingInput, PingOutput
from meritum_core.jobs.contracts._readiness import ReadinessInput, ReadinessReport
from meritum_core.jobs.contracts._subjects import (
    DeleteSubjectInput,
    DeleteSubjectOutput,
)


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

CHECK: Final = WorkflowSpec("check", DEFAULT_QUEUE, CheckInput, CheckOutput)
"""Checks one request; streams AnalysisStatus under PROGRESS_KEY (US-SPR-01, F-09)."""

ESCALATE_CLAIM: Final = WorkflowSpec(
    "escalate_claim", DEFAULT_QUEUE, EscalateClaimInput, EscalateClaimOutput
)
"""Hands one claim of a check to the moderator queue (US-MOD-03)."""

DELETE_SUBJECT: Final = WorkflowSpec(
    "delete_subject", DEFAULT_QUEUE, DeleteSubjectInput, DeleteSubjectOutput
)
"""Deletes the data of one session, user or channel user (US-BEZ-05)."""

READINESS: Final = WorkflowSpec(
    "readiness", DEFAULT_QUEUE, ReadinessInput, ReadinessReport
)
"""Reports what the worker lacks; also sets the READINESS_KEY event (US-WDR-08)."""

EVAL_RUN: Final = WorkflowSpec("eval_run", DEFAULT_QUEUE, EvalRunInput, EvalRunOutput)
"""Runs the golden set or a staff file; ends with eval_run_done (US-OBS-06, F-28)."""

ARCHIVE_PAGE: Final = WorkflowSpec(
    "archive_page", DEFAULT_QUEUE, ArchivePageInput, ArchivePageOutput
)
"""Archives one public page for the citizen who asked (US-KOR-07, F-38)."""

WORKFLOWS: Final[tuple[WorkflowSpec[Any, Any], ...]] = (
    PING,
    CHECK,
    ESCALATE_CLAIM,
    DELETE_SUBJECT,
    READINESS,
    EVAL_RUN,
    ARCHIVE_PAGE,
)
"""Every workflow of the contract (names must be unique)."""
