"""Contract v17: one agreeing fact-checker rating lifts strength to moderate (core#127).

Features:
    US-ZRD-03, ADR-02, ADR-34
"""

from tests.evidence.samples import CLAIM_DATE, cite, review

from meritum_core.checks import contracts as c
from meritum_core.evidence import compute_strength


def _premises(**kw: object) -> c.Premises:
    base: dict[str, object] = {
        "independent_sources": 1,
        "primary_sources": 0,
        "agreement": "consistent",
        "validity": "in_force",
    }
    return c.Premises.model_validate(base | kw)


def test_signatory_reviews_default_to_zero() -> None:
    assert _premises().signatory_reviews == 0


def test_one_signatory_rating_is_at_least_moderate() -> None:
    assert c.strength_for(_premises(signatory_reviews=1)) == "moderate"


def test_without_a_rating_one_secondary_source_stays_weak() -> None:
    assert c.strength_for(_premises()) == "weak"


def test_a_rating_does_not_rescue_conflicting_evidence() -> None:
    p = _premises(signatory_reviews=1, agreement="conflicting")
    assert c.strength_for(p) == "weak"


def test_single_rating_refutation_is_moderate_end_to_end() -> None:
    strength = compute_strength(
        "false", [], claim_date=CLAIM_DATE, reviews=[review("refutes", "demagog")]
    )
    assert strength is not None
    assert (strength.premises.signatory_reviews, strength.level) == (1, "moderate")


def test_one_publisher_with_two_ratings_counts_once_per_publisher() -> None:
    reviews = [review("refutes", "demagog"), review("refutes", "demagog")]
    strength = compute_strength(
        "false", [cite("refutes", "kprm")], claim_date=CLAIM_DATE, reviews=reviews
    )
    assert strength is not None
    assert strength.premises.signatory_reviews == 1
