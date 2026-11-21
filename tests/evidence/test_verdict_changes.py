"""What would change the verdict, computed by one rule from the premises (US-ZRD-11)."""

import pytest
from pydantic import ValidationError
from tests.checks.contracts.samples import CLAIM, REFUTING, SUPPORTING
from tests.evidence.samples import CLAIM_DATE, cite, review

from meritum_core.checks.contracts import Citation, ClaimResult, Verdict
from meritum_core.evidence import compute_verdict_changes

OLD = "2024-01-01T00:00:00+01:00"
GAP = "Nie wiadomo, kto to ogłosił."


@pytest.mark.parametrize(
    ("verdict", "citations", "codes"),
    [
        (
            "confirmed",
            [cite("supports", "demagog"), cite("supports", "oko-press")],
            ["needs_primary_source"],
        ),
        (
            "confirmed",
            [cite("supports", "kprm", "primary")],
            ["needs_second_publisher"],
        ),
        (
            "false",
            [cite("refutes", "demagog")],
            ["needs_primary_source", "needs_second_publisher"],
        ),
        (
            "confirmed",
            [
                cite("supports", "kprm", "primary", published_at=OLD),
                cite("supports", "demagog", published_at=OLD),
            ],
            ["needs_fresh_evidence"],
        ),
        (
            "confirmed",
            [cite("supports", "kprm", "primary"), cite("supports", "demagog")],
            [],
        ),
        (
            "confirmed",
            [cite("supports", "kprm", "primary"), cite("refutes", "demagog")],
            ["needs_resolving_source"],
        ),
        ("insufficient_evidence", [], ["needs_named_source"]),
        ("not_verifiable", [], []),
    ],
    ids=[
        "primary",
        "second-publisher",
        "primary-and-second",
        "fresh",
        "strong-needs-nothing",
        "conflict",
        "nothing-found",
        "not-verifiable",
    ],
)
def test_codes_follow_the_premises(
    verdict: Verdict, citations: list[Citation], codes: list[str]
) -> None:
    assert (
        compute_verdict_changes(
            verdict, citations, claim_date=CLAIM_DATE, unresolved=GAP
        )
        == codes
    )


def test_a_fact_checker_rating_counts_as_a_second_publisher() -> None:
    codes = compute_verdict_changes(
        "false",
        [cite("refutes", "kprm", "primary")],
        claim_date=CLAIM_DATE,
        reviews=[review("refutes", "demagog")],
    )
    assert codes == []


def test_nothing_missing_is_named_without_an_unresolved_note() -> None:
    assert (
        compute_verdict_changes("insufficient_evidence", [], claim_date=CLAIM_DATE)
        == []
    )


def test_contract_accepts_codes_that_follow_the_premises() -> None:
    claim = ClaimResult.model_validate(
        CLAIM | {"would_change_verdict": ["needs_second_publisher"]}
    )
    assert claim.would_change_verdict == ["needs_second_publisher"]


@pytest.mark.parametrize(
    ("changes", "codes"),
    [
        ({}, ["needs_primary_source"]),
        ({}, ["needs_fresh_evidence"]),
        (
            {
                "verdict": "insufficient_evidence",
                "strength": None,
                "citations": [SUPPORTING, REFUTING],
                "unresolved": GAP,
            },
            ["needs_named_source"],
        ),
    ],
    ids=["primary-present", "fresh-evidence", "named-on-conflict"],
)
def test_contract_rejects_codes_against_the_premises(
    changes: dict[str, object], codes: list[str]
) -> None:
    with pytest.raises(ValidationError, match="would change the verdict"):
        ClaimResult.model_validate(CLAIM | changes | {"would_change_verdict": codes})
