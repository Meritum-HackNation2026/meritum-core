"""The answer every channel renders, the moderator hand-off and the cached part of it.

Features:
    US-SPR-06, US-WTY-03, US-MOD-03, ADR-02
"""

from __future__ import annotations

from datetime import datetime
from typing import Annotated, Literal

from pydantic import Field, model_validator

from ._base import _Model
from ._claims import ClaimResult
from ._context import SourceStatusWarning
from ._types import CacheableStatus, CheckStatus


class Escalation(_Model):
    """Hand-off to the moderator queue. 'recommended' means nobody was notified yet.

    Computed on every request, cache hits included: the result cache never stores it.

    Attributes:
        state: recommended, created or updated.
        case_id: the moderator case, once it exists.

    Features:
        US-MOD-03, ADR-02
    """

    state: Literal["recommended", "created", "updated"]
    case_id: Annotated[str | None, Field(pattern=r"^#S-\d+$")] = None

    @model_validator(mode="after")
    def _case_only_when_handed_off(self) -> Escalation:
        if (self.state == "recommended") != (self.case_id is None):
            raise ValueError(
                "a case id exists only after the case was created or updated"
            )
        return self


class CheckResult(_Model):
    """The answer every channel renders. The same normalised input within the result cache's lifetime gets the same substantive result on every channel.

    out_of_scope: an unsupported input type or a request that is not about information. needs_clarification: no claim
    could be extracted. Any factual claim gets a verdict, "insufficient_evidence" included.

    Attributes:
        check_id: the check's id.
        status: done, or one of the statuses that are not verdicts.
        claims: one result per checked claim.
        message: for statuses that are not verdicts, what to do next.
        limitations: what the check could not cover.
        source_warning: a sanctions note about the checked content.
        escalation: the hand-off to the moderator queue.
        corpus_version: the id of the corpus snapshot.
        ai_disclosure: always true; the answer was produced with AI.

    Features:
        US-SPR-06, US-SPR-09, US-BEZ-03, US-BEZ-07, US-OBS-04, US-OBS-05,
        US-WDR-06, ADR-02
    """

    check_id: Annotated[str, Field(min_length=1, max_length=40)]
    status: CheckStatus
    claims: list[ClaimResult] = []
    message: Annotated[
        str | None,
        Field(max_length=400, description="For non-verdict statuses: what to do next."),
    ] = None
    limitations: list[Annotated[str, Field(max_length=300)]] = []
    source_warning: SourceStatusWarning | None = None
    escalation: Escalation | None = None
    corpus_version: Annotated[
        str,
        Field(
            min_length=1,
            max_length=40,
            description="Id of the scheduled corpus snapshot.",
        ),
    ]
    ai_disclosure: Literal[True] = True

    @model_validator(mode="after")
    def _status_rules(self) -> CheckResult:
        if self.status == "done":
            if not self.claims:
                raise ValueError("a finished check has at least one claim")
            if not self.limitations:
                raise ValueError("a finished check states its limitations")
        elif self.claims or self.message is None or not self.message:
            raise ValueError(
                f"{self.status!r} is not a verdict: no claims, and a message instead"
            )
        return self


class CachedResult(_Model):
    """What the result cache keeps: only the substantive part of a CheckResult.

    The key is the normalised input. The entry lives a fixed time, whatever snapshots appear meanwhile.
    Escalation and the repeat counter are not here: they are computed on every request.
    A technical failure is never cached.

    Attributes:
        status: the cached status; never a technical failure.
        claims: the cached claim results.
        message: the cached message for statuses that are not verdicts.
        limitations: the cached limitations.
        source_warning: the cached sanctions note.
        corpus_version: the corpus snapshot the result came from.
        source_ids: the ids of the sources cited in the claims.
        cached_at: when the entry was stored.
        expires_at: when the entry expires.

    Features:
        US-WTY-03, ADR-02
    """

    status: CacheableStatus
    claims: list[ClaimResult] = []
    message: Annotated[str | None, Field(max_length=400)] = None
    limitations: list[Annotated[str, Field(max_length=300)]] = []
    source_warning: SourceStatusWarning | None = None
    corpus_version: Annotated[str, Field(min_length=1, max_length=40)]
    source_ids: Annotated[
        list[str], Field(description="Ids of the sources cited in the claims.")
    ] = []
    cached_at: datetime
    expires_at: datetime

    @model_validator(mode="after")
    def _cache_rules(self) -> CachedResult:
        if self.expires_at <= self.cached_at:
            raise ValueError("a cache entry expires after it was stored")
        cited = {c.source.id for claim in self.claims for c in claim.citations}
        if cited != set(self.source_ids):
            raise ValueError("source_ids are the ids of the cited sources")
        return self
