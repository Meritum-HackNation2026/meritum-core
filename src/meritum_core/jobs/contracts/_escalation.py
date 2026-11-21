"""Models of the `escalate_claim` workflow: hand one claim to moderators.

Features:
    US-MOD-03, ADR-03
"""

from typing import Annotated, Literal, Self

from pydantic import Field, model_validator

from meritum_core.checks import Escalation
from meritum_core.jobs.constants import CHECK_ID_MAX_CHARS, MAX_JUSTIFICATION_CHARS
from meritum_core.jobs.contracts._base import JobModel

EscalationReason = Literal["recommended_clicked", "user_dispute", "cache_hit"]
"""Why a claim goes to moderators: „Przekaż moderatorom”, „Zgłoś błąd”, a cache hit."""


class EscalateClaimInput(JobModel):
    """Input of the `escalate_claim` workflow.

    Attributes:
        check_id: the check the claim belongs to.
        claim_index: position of the claim in the check's result.
        reason: what triggered the escalation.
        justification_masked: the user's masked reason; only for `user_dispute`.

    Features:
        US-MOD-03, ADR-03
    """

    check_id: Annotated[str, Field(min_length=1, max_length=CHECK_ID_MAX_CHARS)]
    claim_index: Annotated[int, Field(ge=0)]
    reason: EscalationReason
    justification_masked: Annotated[
        str | None, Field(min_length=1, max_length=MAX_JUSTIFICATION_CHARS)
    ] = None

    @model_validator(mode="after")
    def _justification_only_for_disputes(self) -> Self:
        is_dispute = self.reason == "user_dispute"
        if is_dispute != (self.justification_masked is not None):
            msg = "a user dispute, and only a dispute, carries a justification"
            raise ValueError(msg)
        return self


class EscalateClaimOutput(JobModel):
    """Output of the `escalate_claim` workflow.

    Attributes:
        escalation: the case created or updated for the claim.

    Features:
        US-MOD-03, ADR-03
    """

    escalation: Escalation
