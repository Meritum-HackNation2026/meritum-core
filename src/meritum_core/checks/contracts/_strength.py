"""Premises behind a verdict and the one rule that turns them into evidence strength.

Features:
    US-ZRD-03, ADR-02
"""

from __future__ import annotations

from datetime import datetime
from typing import Annotated

from pydantic import Field, model_validator

from meritum_core.checks.constants import DEFAULT_MAX_AGE_HOURS, STRONG_MIN_SOURCES

from ._base import _Model
from ._types import Agreement, Strength, Validity


class Premises(_Model):
    """Explicit premises behind a verdict (MSZ: strength must follow from quality, recency, agreement, independence).

    Attributes:
        independent_sources: distinct publishers among the agreeing citations.
        primary_sources: distinct primary-tier publishers among them.
        newest_source_published_at: publication date of the newest agreeing source.
        newest_source_age_hours: hours from that source to the claim date.
        max_age_hours: the catalogue threshold of the newest source.
        validity: the age rule of the agreeing evidence.
        agreement: whether the citations agree or conflict.

    Features:
        US-ZRD-03, US-ZRD-04, US-ZRD-05, ADR-02
    """

    independent_sources: Annotated[
        int,
        Field(
            ge=0,
            description="Distinct publishers (publisher_id) among the citations whose stance agrees with the verdict.",
        ),
    ]
    primary_sources: Annotated[
        int,
        Field(
            ge=0,
            description="Distinct primary-tier publishers among the agreeing citations.",
        ),
    ]
    newest_source_published_at: Annotated[
        datetime | None,
        Field(
            description="Publication date of the newest agreeing source, shown as a date."
        ),
    ] = None
    newest_source_age_hours: Annotated[
        int | None,
        Field(
            ge=0,
            description="Hours from the newest agreeing source to the claim date (ClaimResult.claim_date), not to now; 0 when the source is newer.",
        ),
    ] = None
    max_age_hours: Annotated[
        int,
        Field(
            ge=1, description="Threshold from the catalogue entry of the newest source."
        ),
    ] = DEFAULT_MAX_AGE_HOURS
    validity: Validity = "expires"
    agreement: Agreement


def is_stale(p: Premises) -> bool:
    """Whether expiring evidence is older than its catalogue threshold.

    Args:
        p: the premises of a verdict.

    Returns:
        True when the newest source is past `max_age_hours`.

    Features:
        US-ZRD-05, ADR-02
    """
    return (
        p.validity == "expires"
        and p.newest_source_age_hours is not None
        and p.newest_source_age_hours > p.max_age_hours
    )


def strength_for(p: Premises) -> Strength:
    """The one rule that turns premises into strength. Shown to the user next to the premises.

    Counts cover only publishers whose citations agree with the verdict. Strong: 2+ agreeing
    independent publishers, 1+ of them primary, fresh evidence. Moderate: 2+ agreeing publishers
    or 1 primary, fresh evidence. Weak: one non-primary publisher, or archival evidence.

    Args:
        p: the premises of a verdict.

    Returns:
        "strong", "moderate" or "weak".

    Features:
        US-ZRD-03, ADR-02
    """
    if p.agreement != "consistent" or is_stale(p):
        return "weak"
    if p.independent_sources >= STRONG_MIN_SOURCES and p.primary_sources >= 1:
        return "strong"
    if p.independent_sources >= STRONG_MIN_SOURCES or p.primary_sources >= 1:
        return "moderate"
    return "weak"


class EvidenceStrength(_Model):
    """Strength level together with the premises it follows from.

    Attributes:
        level: the strength derived by `strength_for`.
        premises: the premises it follows from.

    Features:
        US-ZRD-03, ADR-02
    """

    level: Strength
    premises: Premises

    @model_validator(mode="after")
    def _level_follows_premises(self) -> EvidenceStrength:
        if self.level != strength_for(self.premises):
            raise ValueError(
                f"strength must be {strength_for(self.premises)!r} for these premises"
            )
        return self
