"""Premises and evidence strength computed from citations with a stance (ADR-05).

Strength never comes from a prompt or a model's claim: the premises are counted here
from the citations and fact-checkers' ratings, and the level comes from the contract's
``strength_for``, the same rule its validator applies.

Features:
    US-ZRD-03, US-ZRD-04, US-SPR-04, US-SPR-05, F-15, ADR-05
"""

from collections.abc import Sequence
from datetime import date, datetime, time, timedelta
from operator import itemgetter

from meritum_core.checks.contracts import (
    AGREEING_STANCE,
    SETTLING,
    Citation,
    ClaimReviewPremise,
    EvidenceStrength,
    Premises,
    Validity,
    Verdict,
    strength_for,
)


def settle_verdict(
    verdict: Verdict,
    citations: Sequence[Citation],
    reviews: Sequence[ClaimReviewPremise] = (),
) -> Verdict:
    """Keep the proposed verdict unless credible sources conflict.

    Args:
        verdict: The verdict proposed for the claim.
        citations: The citations with their stance.
        reviews: Fact-checkers' ratings used as premises.

    Returns:
        ``insufficient_evidence`` when current evidence both supports and refutes the
        claim, otherwise ``verdict``.

    Features:
        US-ZRD-04, US-SPR-04, US-SPR-05, F-15, ADR-05
    """
    return "insufficient_evidence" if _conflicting(citations, reviews) else verdict


def compute_premises(
    verdict: Verdict,
    citations: Sequence[Citation],
    *,
    claim_date: date,
    reviews: Sequence[ClaimReviewPremise] = (),
) -> Premises:
    """Count the premises of a verdict from the evidence that agrees with it.

    Superseded citations are left out. Independence is counted per ``publisher_id``;
    a fact-checker's rating counts as one secondary-tier publisher (ADR-34). Age runs
    from the newest agreeing source to the start of the claim date, taken in that
    source's own UTC offset. The validity is the newest non-expiring one among the
    agreeing citations, so an older article never ages out law in force; it is
    ``expires`` only when all agreeing evidence expires. A non-settling verdict has
    no agreeing stance, so its premises count no publishers.

    Args:
        verdict: The verdict whose agreeing stance is counted.
        citations: The citations with their stance and validity.
        claim_date: The date the claim refers to.
        reviews: Fact-checkers' ratings used as premises.

    Returns:
        The premises the strength rule reads.

    Features:
        US-ZRD-03, US-ZRD-04, F-15, ADR-05
    """
    stance = AGREEING_STANCE.get(verdict)
    agreeing = [c for c in _current(citations) if c.stance == stance]
    agreeing_reviews = [r for r in reviews if r.stance == stance]
    publishers = {c.source.publisher_id for c in agreeing}
    publishers |= {r.publisher_id for r in agreeing_reviews}
    primary = {c.source.publisher_id for c in agreeing if c.source.tier == "primary"}
    evidence: list[tuple[datetime | None, Validity]] = [
        (c.source.published_at, c.validity) for c in agreeing
    ]
    evidence += [(r.reviewed_at, "expires") for r in agreeing_reviews]
    newest_at, _ = _newest(evidence)
    # Evidence that does not expire (law in force...) keeps the premises fresh.
    _, validity = _newest([e for e in evidence if e[1] != "expires"])
    return Premises(
        independent_sources=len(publishers),
        primary_sources=len(primary),
        newest_source_published_at=newest_at,
        newest_source_age_hours=_age_hours(newest_at, claim_date),
        validity=validity,
        agreement="conflicting" if _conflicting(citations, reviews) else "consistent",
    )


def compute_strength(
    verdict: Verdict,
    citations: Sequence[Citation],
    *,
    claim_date: date,
    reviews: Sequence[ClaimReviewPremise] = (),
) -> EvidenceStrength | None:
    """Derive the strength of a verdict with the single rule of the contract.

    Args:
        verdict: The verdict of the claim.
        citations: The citations with their stance and validity.
        claim_date: The date the claim refers to.
        reviews: Fact-checkers' ratings used as premises.

    Returns:
        The strength with its premises, or None when the verdict does not settle the
        claim or the sources conflict.

    Features:
        US-ZRD-03, US-ZRD-04, F-15, ADR-05
    """
    if verdict not in SETTLING or _conflicting(citations, reviews):
        return None
    premises = compute_premises(
        verdict, citations, claim_date=claim_date, reviews=reviews
    )
    return EvidenceStrength(level=strength_for(premises), premises=premises)


def _current(citations: Sequence[Citation]) -> list[Citation]:
    return [c for c in citations if c.validity != "superseded"]


def _conflicting(
    citations: Sequence[Citation], reviews: Sequence[ClaimReviewPremise]
) -> bool:
    stances = {c.stance for c in _current(citations)} | {r.stance for r in reviews}
    return {"supports", "refutes"} <= stances


def _newest(
    evidence: list[tuple[datetime | None, Validity]],
) -> tuple[datetime | None, Validity]:
    dated = [(at, validity) for at, validity in evidence if at is not None]
    if dated:
        return max(dated, key=itemgetter(0))
    # Undated evidence only: its validity still applies, it just has no age.
    return evidence[0] if evidence else (None, "expires")


def _age_hours(published_at: datetime | None, claim_date: date) -> int | None:
    if published_at is None:
        return None
    claim_start = datetime.combine(claim_date, time.min, tzinfo=published_at.tzinfo)
    return max(0, (claim_start - published_at) // timedelta(hours=1))
