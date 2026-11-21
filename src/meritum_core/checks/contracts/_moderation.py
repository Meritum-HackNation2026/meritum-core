"""Moderator cases: groups of similar unanswered or disputed claims.

Features:
    US-MOD-01, US-MOD-02, ADR-02
"""

from __future__ import annotations

from datetime import datetime
from typing import Annotated, Literal

from pydantic import Field, model_validator

from ._base import _Model
from ._types import CaseReason


class CaseClaim(_Model):
    """One claim in a case and the checks that asked it: unanswered ("insufficient_evidence"), or disputed by a user.

    Attributes:
        claim: the claim as asked.
        check_ids: the checks that asked it.

    Features:
        US-MOD-01, US-MOD-02, ADR-02
    """

    claim: Annotated[str, Field(min_length=5, max_length=500)]
    check_ids: Annotated[list[str], Field(min_length=1)]


class ModeratorCase(_Model):
    """One case per group of similar unanswered claims. Similarity is measured per claim; a repeated claim joins the case.

    Attributes:
        id: the case id, e.g. #S-12.
        state: open, answered or closed.
        reasons: why the case exists, each listed once.
        high_risk_topic: the high-risk topic that matched.
        high_risk_classified_by: how the topic was classified.
        summary: a short summary for the moderator.
        claims: the grouped claims.
        distinct_askers: distinct sessions or users who asked.
        first_seen: when the first claim arrived.
        last_seen: when the latest claim arrived.
        assignee_role: the staff role the case is assigned to.

    Features:
        US-MOD-01, US-MOD-02, US-MOD-05, US-MOD-06, US-MOD-07, US-OBS-03, ADR-02,
        ADR-35
    """

    id: Annotated[str, Field(pattern=r"^#S-\d+$")]
    state: Literal["open", "answered", "closed"]
    reasons: Annotated[list[CaseReason], Field(min_length=1)]
    high_risk_topic: Annotated[
        str | None,
        Field(
            max_length=80,
            description="Topic from the admin's high-risk list that matched.",
        ),
    ] = None
    high_risk_classified_by: Annotated[
        Literal["embeddings", "keywords"] | None,
        Field(
            description="Embedding similarity to the admin list above a threshold, or the keyword list as a fallback (ADR-35)."
        ),
    ] = None
    summary: Annotated[str, Field(min_length=5, max_length=300)]
    claims: Annotated[list[CaseClaim], Field(min_length=1)]
    distinct_askers: Annotated[
        int,
        Field(
            ge=1,
            description="Distinct sessions or users who asked; raises the case's priority only, never decides whether it exists.",
        ),
    ] = 1
    first_seen: datetime
    last_seen: datetime
    assignee_role: Literal["moderator", "analyst"] = "moderator"

    @model_validator(mode="after")
    def _case_rules(self) -> ModeratorCase:
        if len(set(self.reasons)) != len(self.reasons):
            raise ValueError("each reason is listed once")
        high_risk = "high_risk" in self.reasons
        if high_risk != (self.high_risk_topic is not None) or high_risk != (
            self.high_risk_classified_by is not None
        ):
            raise ValueError(
                "a high-risk case names the matched topic and how it was classified"
            )
        return self

    @property
    def check_ids(self) -> list[str]:
        """Distinct checks grouped by the case, in order of appearance."""
        return list(dict.fromkeys(i for c in self.claims for i in c.check_ids))

    @property
    def similar_count(self) -> int:
        """How many checks the case groups."""
        return len(self.check_ids)
