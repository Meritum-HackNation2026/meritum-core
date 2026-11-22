"""Job contract between meritum-backend (enqueues) and meritum-worker (runs).

Every input and output is one portable JSON object with `contract_version`.

Features:
    US-SPR-01, US-SPR-02, US-MOD-03, US-BEZ-05, US-WDR-08, US-OBS-06, F-09, F-28, ADR-03
"""

from meritum_core.jobs.constants import (
    APPLICATION_NAME,
    CONTRACT_VERSION,
    DEFAULT_QUEUE,
)
from meritum_core.jobs.contracts._check import CheckInput, CheckOutput
from meritum_core.jobs.contracts._escalation import (
    EscalateClaimInput,
    EscalateClaimOutput,
    EscalationReason,
)
from meritum_core.jobs.contracts._eval_run import EvalRunInput, EvalRunOutput
from meritum_core.jobs.contracts._ping import PingInput, PingOutput
from meritum_core.jobs.contracts._readiness import ReadinessInput, ReadinessReport
from meritum_core.jobs.contracts._subjects import (
    DeleteSubjectInput,
    DeleteSubjectOutput,
    SubjectKind,
)
from meritum_core.jobs.contracts._workflows import (
    CHECK,
    DELETE_SUBJECT,
    ESCALATE_CLAIM,
    EVAL_RUN,
    PING,
    READINESS,
    WORKFLOWS,
    WorkflowSpec,
)

__all__ = [
    "APPLICATION_NAME",
    "CHECK",
    "CONTRACT_VERSION",
    "DEFAULT_QUEUE",
    "DELETE_SUBJECT",
    "ESCALATE_CLAIM",
    "EVAL_RUN",
    "PING",
    "READINESS",
    "WORKFLOWS",
    "CheckInput",
    "CheckOutput",
    "DeleteSubjectInput",
    "DeleteSubjectOutput",
    "EscalateClaimInput",
    "EscalateClaimOutput",
    "EscalationReason",
    "EvalRunInput",
    "EvalRunOutput",
    "PingInput",
    "PingOutput",
    "ReadinessInput",
    "ReadinessReport",
    "SubjectKind",
    "WorkflowSpec",
]
