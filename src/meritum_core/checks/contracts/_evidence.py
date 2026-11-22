"""Evidence counted into premises in one place, shared by validator and compute.

Features:
    US-ZRD-03, US-ZRD-04, F-15, ADR-05, ADR-34
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from meritum_core.checks.constants import AGREEING_STANCE

from ._strength import is_expired

if TYPE_CHECKING:
    from collections.abc import Sequence
    from datetime import date

    from ._sources import Citation, ClaimReviewPremise
    from ._types import PublisherId, Verdict


@dataclass(frozen=True)
class AgreeingEvidence:
    """Current evidence whose stance agrees with a verdict.

    Attributes:
        citations: non-superseded citations with the verdict's stance.
        reviews: fact-checkers' ratings with the verdict's stance.
        publishers: distinct publishers among both; a rating counts as one
            secondary-tier publisher (ADR-34).
        primary: distinct primary-tier publishers among the citations.

    Features:
        US-ZRD-03, US-ZRD-04, ADR-05, ADR-34
    """

    citations: list[Citation]
    reviews: list[ClaimReviewPremise]
    publishers: set[PublisherId]
    primary: set[PublisherId]


def current_citations(citations: Sequence[Citation]) -> list[Citation]:
    """Citations that were not superseded by newer evidence.

    Args:
        citations: the citations with their validity.

    Returns:
        The citations still in force.

    Features:
        US-ZRD-10, ADR-05
    """
    return [c for c in citations if c.validity != "superseded"]


def agreeing_evidence(
    verdict: Verdict,
    citations: Sequence[Citation],
    reviews: Sequence[ClaimReviewPremise],
) -> AgreeingEvidence:
    """Pick the evidence that agrees with a verdict and count its publishers.

    Args:
        verdict: the verdict whose agreeing stance is counted; a non-settling one
            agrees with nothing.
        citations: the citations with their stance and validity.
        reviews: fact-checkers' ratings used as premises.

    Returns:
        The agreeing citations and ratings with their publishers.

    Features:
        US-ZRD-03, US-ZRD-04, F-15, ADR-05, ADR-34
    """
    stance = AGREEING_STANCE.get(verdict)
    agreeing = [c for c in current_citations(citations) if c.stance == stance]
    agreeing_reviews = [r for r in reviews if r.stance == stance]
    publishers = {c.source.publisher_id for c in agreeing}
    publishers |= {r.publisher_id for r in agreeing_reviews}
    primary = {c.source.publisher_id for c in agreeing if c.source.tier == "primary"}
    return AgreeingEvidence(agreeing, agreeing_reviews, publishers, primary)


def sources_conflict(
    citations: Sequence[Citation],
    reviews: Sequence[ClaimReviewPremise],
    claim_date: date | None,
) -> bool:
    """Whether current evidence both supports and refutes the claim.

    Args:
        citations: the citations with their stance and validity.
        reviews: fact-checkers' ratings used as premises.
        claim_date: the date the claim refers to; expired evidence never conflicts
            with fresh evidence (US-ZRD-10). None keeps every current citation.

    Returns:
        True when both a supporting and a refuting source remain.

    Features:
        US-ZRD-04, US-ZRD-10, F-15, ADR-05
    """
    fresh = [
        c
        for c in current_citations(citations)
        if claim_date is None or not is_expired(c, claim_date)
    ]
    stances = {c.stance for c in fresh} | {r.stance for r in reviews}
    return {"supports", "refutes"} <= stances
