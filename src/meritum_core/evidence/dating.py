"""Claim date and the verdict on evidence that was true once (US-ZRD-05, US-ZRD-10).

Evidence age runs from the date the claim refers to, never from today.

Features:
    US-ZRD-05, US-ZRD-10, F-15, ADR-25
"""

from collections.abc import Sequence
from datetime import date, datetime

from meritum_core.checks.contracts import (
    DEFAULT_MAX_AGE_HOURS,
    Citation,
    ClaimDateSource,
    TechniqueCode,
    Verdict,
    is_stale,
)
from meritum_core.evidence.constants import OUTDATED_VERDICTS
from meritum_core.evidence.strength import compute_premises


def resolve_claim_date(
    text_date: date | None, input_published_at: datetime | None, *, today: date
) -> tuple[date, ClaimDateSource]:
    """Pick the date the claim refers to and say where it came from.

    Args:
        text_date: A date stated in the claim's text.
        input_published_at: When the checked input (post, article) was published.
        today: The date of the check.

    Returns:
        The text's date, else the input's publication date in its own offset,
        else today; with ``text``, ``input_published_at`` or ``today``.

    Features:
        US-ZRD-05, F-15, ADR-25
    """
    if text_date is not None:
        return text_date, "text"
    if input_published_at is not None:
        return input_published_at.date(), "input_published_at"
    return today, "today"


def outdated_verdict(
    verdict: Verdict,
    citations: Sequence[Citation],
    *,
    claim_date: date,
    present_tense: bool = False,
    max_age_hours: int = DEFAULT_MAX_AGE_HOURS,
) -> tuple[Verdict, TechniqueCode | None, bool]:
    """Adjust a verdict for evidence that was true once but is not any more.

    A claim refuted by evidence that superseded its support (a superseded
    supporting citation) keeps its verdict
    with technique ``outdated`` (never ``insufficient_evidence``: superseded
    evidence does not conflict). A present-tense claim confirmed only by stale
    expiring evidence becomes ``misleading``, ``outdated`` and archival. A claim
    with an explicit past date is judged by the evidence valid on that date.

    Args:
        verdict: The verdict settled from current evidence.
        citations: The citations with their validity set.
        claim_date: The date the claim refers to.
        present_tense: Whether the claim speaks about the present.
        max_age_hours: The catalogue threshold of the newest source.

    Returns:
        The verdict, its technique (or None) and whether the evidence is archival.

    Features:
        US-ZRD-05, US-ZRD-10, F-15, ADR-25
    """
    support_replaced = any(
        c.validity == "superseded" and c.stance == "supports" for c in citations
    )
    if support_replaced and verdict in OUTDATED_VERDICTS:
        return verdict, "outdated", False
    premises = compute_premises(
        verdict, citations, claim_date=claim_date, max_age_hours=max_age_hours
    )
    stale = is_stale(premises)
    if stale and present_tense and verdict == "confirmed":
        return "misleading", "outdated", True
    return verdict, None, stale
