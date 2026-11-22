"""The computed strength always passes the contract validator, so the two cannot drift."""

from typing import Any

import pytest
from pydantic import ValidationError
from tests.evidence.samples import CLAIM, CLAIM_DATE, EXAMPLES, cite, review

from meritum_core.checks.contracts import (
    Citation,
    ClaimResult,
    ClaimReviewPremise,
    Verdict,
)
from meritum_core.evidence import compute_strength, settle_verdict

CASES: dict[str, tuple[Verdict, list[Citation], list[ClaimReviewPremise]]] = {
    "strong": (
        "confirmed",
        [cite("supports", "kprm", "primary"), cite("supports", "demagog")],
        [],
    ),
    "stale": (
        "false",
        [cite("refutes", "demagog", published_at="2020-01-01T00:00:00+01:00")],
        [],
    ),
    "in-force": (
        "false",
        [cite("refutes", "kprm", "primary", validity="in_force")],
        [],
    ),
    "law-and-old-article": (
        "confirmed",
        [
            cite(
                "supports",
                "kprm",
                "primary",
                published_at="1997-07-16T00:00:00+02:00",
                validity="in_force",
            ),
            cite("supports", "demagog", published_at="2020-01-01T00:00:00+01:00"),
        ],
        [],
    ),
    "expired-next-to-fresh": (
        "false",
        [
            cite(
                "supports", "kprm", "primary", published_at="2020-01-01T00:00:00+01:00"
            ),
            cite("refutes", "demagog"),
        ],
        [],
    ),
    "review-only": ("false", [], [review("refutes", "demagog")]),
    "conflict": (
        "confirmed",
        [cite("supports", "kprm", "primary")],
        [review("refutes", "demagog")],
    ),
}


@pytest.mark.parametrize("case", CASES)
def test_computed_strength_passes_the_contract(case: str) -> None:
    proposed, citations, reviews = CASES[case]
    verdict = settle_verdict(proposed, citations, reviews, claim_date=CLAIM_DATE)
    strength = compute_strength(
        verdict, citations, claim_date=CLAIM_DATE, reviews=reviews
    )
    ClaimResult.model_validate(
        CLAIM
        | {
            "claim_date": CLAIM_DATE,
            "verdict": verdict,
            "strength": strength,
            "citations": citations,
            "claim_review_premises": reviews,
            "archival": strength is not None and case == "stale",
            "unresolved": "Źródła podają sprzeczne informacje."
            if strength is None
            else None,
        }
    )


def test_contract_rejects_confirmed_next_to_a_refuting_citation() -> None:
    citations = [cite("supports", "kprm", "primary"), cite("refutes", "demagog")]
    with pytest.raises(ValidationError, match="conflicting sources"):
        ClaimResult.model_validate(
            CLAIM
            | {
                "verdict": "confirmed",
                "strength": compute_strength(
                    "confirmed", citations[:1], claim_date=CLAIM_DATE
                ),
                "citations": citations,
            }
        )


def _example_claims() -> list[dict[str, Any]]:
    return [
        claim
        for example in EXAMPLES.values()
        if isinstance(example, dict)
        for claim in example.get("claims", [])
        if claim.get("strength")
    ]


@pytest.mark.parametrize("claim", _example_claims())
def test_example_strength_is_the_computed_one(claim: dict[str, Any]) -> None:
    parsed = ClaimResult.model_validate(claim)
    computed = compute_strength(
        parsed.verdict,
        parsed.citations,
        claim_date=parsed.claim_date,
        reviews=parsed.claim_review_premises,
    )
    assert computed == parsed.strength
