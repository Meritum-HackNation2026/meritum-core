"""The MSZ rules a ClaimResult must satisfy, one small check per rule.

Features:
    US-ZRD-03, US-ZRD-04, US-ZRD-05, US-ZRD-10, ADR-02
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from meritum_core.checks.constants import AGREEING_STANCE, SETTLING

from ._strength import is_stale

if TYPE_CHECKING:
    from ._claims import ClaimResult
    from ._sources import Citation
    from ._types import Stance


def check_verdict_rules(claim: ClaimResult) -> None:
    """Raise on the first rule the claim breaks, in the order of the MSZ brief.

    Args:
        claim: the claim result being validated.

    Raises:
        ValueError: the claim breaks a rule; the message names it.

    Features:
        US-ZRD-03, US-ZRD-04, US-ZRD-05, US-ZRD-10, ADR-02
    """
    current = [c for c in claim.citations if c.validity != "superseded"]
    _superseded_next_to_newer(claim.citations, current)
    stances = {c.stance for c in current}
    conflicting = {"supports", "refutes"} <= stances
    _conflict_rules(claim, conflicting=conflicting)
    if (claim.claim_date is None) != (claim.claim_date_source is None):
        raise ValueError("a claim date comes with where it was taken from")
    _settling_rules(claim, stances)
    _premises_rules(claim, current, conflicting=conflicting)
    if claim.verdict == "insufficient_evidence" and (
        claim.unresolved is None or not claim.unresolved
    ):
        raise ValueError(
            "'insufficient_evidence' must say what could not be established"
        )
    _age_rules(claim)


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


def _conflict_rules(claim: ClaimResult, *, conflicting: bool) -> None:
    insufficient = claim.verdict == "insufficient_evidence"
    if conflicting and (not insufficient or claim.strength is not None):
        raise ValueError(
            "conflicting sources give 'insufficient_evidence' with both sides cited "
            "and no strength"
        )
    if insufficient and claim.citations and not conflicting:
        raise ValueError(
            "'insufficient_evidence' carries citations only when credible sources "
            "conflict"
        )


def _settling_rules(claim: ClaimResult, stances: set[Stance]) -> None:
    settling = claim.verdict in SETTLING
    if claim.strength is not None and not settling:
        raise ValueError(
            "only a settling verdict (confirmed, false, misleading) has a strength"
        )
    if not settling:
        return
    if not claim.citations or claim.strength is None:
        raise ValueError(f"verdict {claim.verdict!r} needs citations and premises")
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
    agreeing = [c for c in current if c.stance == AGREEING_STANCE[claim.verdict]]
    publishers = {c.source.publisher_id for c in agreeing}
    primary = {c.source.publisher_id for c in agreeing if c.source.tier == "primary"}
    if p.agreement != ("conflicting" if conflicting else "consistent"):
        raise ValueError("agreement must follow from the citation stances")
    if (p.independent_sources, p.primary_sources) != (len(publishers), len(primary)):
        raise ValueError(
            "independent and primary sources are counted per publisher among the "
            "citations that agree with the verdict"
        )
    if p.validity != "expires" and p.validity not in {c.validity for c in agreeing}:
        raise ValueError("the premises' validity must come from an agreeing citation")


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
