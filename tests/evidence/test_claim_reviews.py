"""Fact-checkers' ClaimReview ratings mapped to a stance, then a premise or context."""

from datetime import UTC, datetime, timedelta

import pytest
from tests.evidence.samples import CLAIM_DATE, REVIEW

from meritum_core.checks.contracts import (
    ClaimReviewContext,
    ClaimReviewPremise,
    Stance,
)
from meritum_core.evidence import (
    FoundClaimReview,
    compute_strength,
    normalize_rating,
    rate_review,
    rating_stance,
)

FETCHED = datetime(2026, 11, 21, 12, tzinfo=UTC)


def found(
    rating: str, publisher_id: str = "demagog", **extra: object
) -> FoundClaimReview:
    """A rating as the API returned it, with the publisher's catalogue facts."""
    fields = {k: v for k, v in REVIEW.items() if k != "stance"}
    return FoundClaimReview.model_validate(
        fields | {"rating": rating, "publisher_id": publisher_id} | extra
    )


def test_normalize_rating_folds_case_whitespace_and_diacritics() -> None:
    assert normalize_rating("  CZĘŚCIOWA \u00a0 Prawda ") == "czesciowa prawda"
    assert normalize_rating("Fałsz") == normalize_rating("falsz")


@pytest.mark.parametrize(
    ("publisher_id", "rating", "stance"),
    [
        ("demagog", "Fałsz", "refutes"),
        ("demagog", "FALSE", "refutes"),
        ("demagog", "Prawda", "supports"),
        ("demagog", "true", "supports"),
        ("demagog", "Częściowa prawda", "context"),
        ("demagog", "Manipulacja", "context"),
        ("afp", "Misleading", "context"),
        ("afp", "Fałsz", "refutes"),
        ("demagog", "Nie do końca", "context"),
        ("unknown-checker", "Fałsz", "context"),
    ],
)
def test_rating_stance_reads_the_publishers_table(
    publisher_id: str, rating: str, stance: Stance
) -> None:
    assert rating_stance(publisher_id, rating) == stance


def test_decisive_rating_becomes_a_premise_with_the_verbatim_rating() -> None:
    rated = rate_review(found("Fałsz"), cache_control="max-age=3600")
    assert isinstance(rated.evidence, ClaimReviewPremise)
    assert rated.evidence.stance == "refutes"
    assert rated.evidence.rating == "Fałsz"


def test_rating_outside_the_table_stays_context_with_its_link() -> None:
    rated = rate_review(found("Nie do końca"), cache_control="max-age=3600")
    assert isinstance(rated.evidence, ClaimReviewContext)
    assert str(rated.evidence.url) == REVIEW["url"]


def test_context_rating_keeps_its_exact_wording() -> None:
    rated = rate_review(found("Częściowa prawda"), cache_control="max-age=60")
    assert rated.evidence.rating == "Częściowa prawda"


def test_rating_of_a_non_signatory_is_never_a_premise() -> None:
    rated = rate_review(found("Fałsz", signatory_of=[]), cache_control="max-age=60")
    assert isinstance(rated.evidence, ClaimReviewContext)


@pytest.mark.parametrize(
    ("cache_control", "kept_for"),
    [
        ("public, max-age=3600", timedelta(hours=1)),
        ("MAX-AGE=60, must-revalidate", timedelta(minutes=1)),
        ("no-store, max-age=3600", timedelta(0)),
        ("no-cache", timedelta(0)),
        ("", timedelta(0)),
        (None, timedelta(0)),
    ],
)
def test_rating_is_kept_no_longer_than_the_cache_headers_allow(
    cache_control: str | None, kept_for: timedelta
) -> None:
    rated = rate_review(found("Fałsz", fetched_at=FETCHED), cache_control=cache_control)
    assert rated.keep_until == FETCHED + kept_for


def test_one_fact_checker_alone_counts_as_one_secondary_publisher() -> None:
    premise = rate_review(found("Fałsz"), cache_control="max-age=60").evidence
    assert isinstance(premise, ClaimReviewPremise)
    strength = compute_strength("false", [], claim_date=CLAIM_DATE, reviews=[premise])
    assert strength is not None
    assert strength.premises.independent_sources == 1
    assert strength.premises.primary_sources == 0
    assert strength.level != "strong"
