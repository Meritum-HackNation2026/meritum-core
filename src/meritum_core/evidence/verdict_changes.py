"""What would change the verdict, counted from the same citations as its strength.

Every channel gets the same codes because they come from the contract's
``verdict_changes_for``, the rule its validator applies, never from a model.

Features:
    US-ZRD-11, F-17, ADR-05
"""

from collections.abc import Sequence
from datetime import date

from meritum_core.checks.contracts import (
    Citation,
    ClaimReviewPremise,
    Verdict,
    VerdictChange,
    verdict_changes_for,
)
from meritum_core.evidence.strength import compute_premises


def compute_verdict_changes(
    verdict: Verdict,
    citations: Sequence[Citation],
    *,
    claim_date: date,
    reviews: Sequence[ClaimReviewPremise] = (),
    unresolved: str | None = None,
) -> list[VerdictChange]:
    """List what would change the verdict, deterministically, from its premises.

    Args:
        verdict: The verdict of the claim.
        citations: The citations with their stance and validity.
        claim_date: The date the claim refers to.
        reviews: Fact-checkers' ratings used as premises.
        unresolved: What could not be established.

    Returns:
        The codes of contract v4, in a fixed order; empty when nothing is missing.

    Features:
        US-ZRD-11, F-17, ADR-05
    """
    premises = compute_premises(
        verdict, citations, claim_date=claim_date, reviews=reviews
    )
    return verdict_changes_for(
        verdict,
        premises,
        unresolved,
        conflicting=premises.agreement == "conflicting",
    )
