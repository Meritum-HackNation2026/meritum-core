"""The MSZ rules a ClaimResult must satisfy, one small check per rule.

Features:
    US-ZRD-03, US-ZRD-04, US-ZRD-05, US-ZRD-10, US-ZRD-11, ADR-02, ADR-34
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from meritum_core.checks.constants import AGREEING_STANCE, SETTLING

from ._strength import is_stale
from ._verdict_changes import verdict_changes_for

if TYPE_CHECKING:
    from ._claims import ClaimResult
    from ._sources import Citation, ClaimReviewPremise
    from ._types import PublisherId, Stance


def check_verdict_rules(claim: ClaimResult) -> None:
    """Raise on the first rule the claim breaks, in the order of the MSZ brief.

    Args:
        claim: the claim result being validated.

    Raises:
        ValueError: the claim breaks a rule; the message names it.

    Features:
        US-ZRD-03, US-ZRD-04, US-ZRD-05, US-ZRD-10, US-ZRD-11, ADR-02, ADR-34
    """
    current = [c for c in claim.citations if c.validity != "superseded"]
    _superseded_next_to_newer(claim.citations, current)
    reviews = claim.claim_review_premises
    stances = {c.stance for c in current} | {r.stance for r in reviews}
    conflicting = {"supports", "refutes"} <= stances
    _conflict_rules(claim, conflicting=conflicting)
    _settling_rules(claim, stances)
    # ClaimReview-only premises have no citation validity, so they stay "expires".
    _premises_rules(claim, current, conflicting=conflicting)
    if claim.verdict == "insufficient_evidence" and (
        claim.unresolved is None or not claim.unresolved
    ):
        raise ValueError(
            "'insufficient_evidence' must say what could not be established"
        )
    _age_rules(claim)
    _changes_rules(claim, conflicting=conflicting)


def _superseded_next_to_newer(
    citations: list[Citation], current: list[Citation]
) -> None:
    for old in (c for c in citations if c.validity == "superseded"):
        published = old.source.published_at
        if published is None or not any(
            n.source.published_at is not None and n.source.published_at > published
            for n in current
        ):
            raise ValueError(
                "superseded evidence is shown only next to newer evidence that "
                "replaced it"
            )


def _has_evidence(claim: ClaimResult) -> bool:
    return bool(claim.citations or claim.claim_review_premises)


def _conflict_rules(claim: ClaimResult, *, conflicting: bool) -> None:
    insufficient = claim.verdict == "insufficient_evidence"
    if conflicting and (not insufficient or claim.strength is not None):
        raise ValueError(
            "conflicting sources give 'insufficient_evidence' with both sides cited "
            "and no strength"
        )
    if insufficient and _has_evidence(claim) and not conflicting:
        raise ValueError(
            "'insufficient_evidence' carries citations or ratings only when "
            "credible sources conflict"
        )


def _settling_rules(claim: ClaimResult, stances: set[Stance]) -> None:
    settling = claim.verdict in SETTLING
    if claim.strength is not None and not settling:
        raise ValueError(
            "only a settling verdict (confirmed, false, misleading) has a strength"
        )
    if not settling:
        return
    if not _has_evidence(claim) or claim.strength is None:
        raise ValueError(
            f"verdict {claim.verdict!r} needs citations or fact-checkers' ratings,"
            " and premises"
        )
    if claim.verdict == "confirmed" and "supports" not in stances:
        raise ValueError("'confirmed' needs a supporting citation")
    if claim.verdict == "false" and "refutes" not in stances:
        raise ValueError("'false' needs a refuting citation")
    has_context = "context" in stances and claim.technique is not None
    if claim.verdict == "misleading" and not has_context:
        raise ValueError(
            "'misleading' needs a context citation and the technique it uses"
        )


def _premises_rules(
    claim: ClaimResult, current: list[Citation], *, conflicting: bool
) -> None:
    if claim.strength is None or claim.verdict not in SETTLING:
        return
    p = claim.strength.premises
    stance = AGREEING_STANCE[claim.verdict]
    agreeing = [c for c in current if c.stance == stance]
    reviews = _agreeing_reviews(claim.claim_review_premises, stance)
    publishers = {c.source.publisher_id for c in agreeing} | reviews
    primary = {c.source.publisher_id for c in agreeing if c.source.tier == "primary"}
    if p.agreement != ("conflicting" if conflicting else "consistent"):
        raise ValueError("agreement must follow from the citation stances")
    if (p.independent_sources, p.primary_sources) != (len(publishers), len(primary)):
        raise ValueError(
            "independent and primary sources are counted per publisher among the "
            "citations and fact-checkers' ratings that agree with the verdict"
        )
    if p.validity != "expires" and p.validity not in {c.validity for c in agreeing}:
        raise ValueError("the premises' validity must come from an agreeing citation")


def _agreeing_reviews(
    reviews: list[ClaimReviewPremise], stance: Stance
) -> set[PublisherId]:
    # A fact-checker's rating counts as one secondary-tier publisher (ADR-34).
    return {r.publisher_id for r in reviews if r.stance == stance}


def _age_rules(claim: ClaimResult) -> None:
    if claim.strength is None:
        return
    if is_stale(claim.strength.premises) and not claim.archival:
        raise ValueError(
            "evidence older than the catalogue threshold must be marked archival"
        )
    if claim.archival and claim.strength.premises.validity != "expires":
        raise ValueError(
            "evidence that does not expire (law in force, page updated in place, past"
            " event) is never archival"
        )


def _changes_rules(claim: ClaimResult, *, conflicting: bool) -> None:
    # Subset, not equality: a channel may name fewer codes, never one the premises deny.
    allowed = verdict_changes_for(
        claim.verdict,
        claim.strength.premises if claim.strength else None,
        claim.unresolved,
        conflicting=conflicting,
    )
    if not set(claim.would_change_verdict) <= set(allowed):
        raise ValueError(
            f"what would change the verdict must follow from the premises: {allowed}"
        )
