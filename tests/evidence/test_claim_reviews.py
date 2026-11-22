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
    assert normalize_rating("Fałsz.") == "falsz"


def test_rating_with_its_explanation_becomes_a_premise_with_the_whole_rating() -> None:
    rating = "Fałsz. Szczepionki nie zmieniają kodu genetycznego."
    rated = rate_review(found(rating), cache_control="max-age=3600")
    assert isinstance(rated.evidence, ClaimReviewPremise)
    assert rated.evidence.stance == "refutes"
    assert rated.evidence.rating == rating


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
        # Dev, 2026-11-22 (core#154): Demagog's ratings as Fact Check API sends them.
        ("demagog", "Fałsz.", "refutes"),
        ("demagog", "Prawda.", "supports"),
        (
            "demagog",
            "Fałsz. COVID-19 nie rozprzestrzenia się falami radiowymi.",
            "refutes",
        ),
        ("demagog", "Prawda! Dane GUS to potwierdzają.", "supports"),
        ("demagog", "Brakujący kontekst.", "context"),
        # Labels of matched ratings that make a claim misleading (worker#280).
        ("demagog", "Częściowy fałsz", "context"),
        ("demagog", "Nieprawda", "refutes"),
        ("afp", "Częściowo fałsz", "context"),
        ("afp", "Partly false", "context"),
        ("afp", "Missing context", "context"),
        ("afp", "Wprowadzające w błąd", "context"),
        ("fakenews-pl", "Manipulacja", "context"),
        ("fakenews-pl", "Fake news", "refutes"),
        ("konkret24", "Wprowadza w błąd", "context"),
        ("demagog", "Fałszywy alarm w tytule", "context"),
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


@pytest.mark.parametrize(
    ("publisher_id", "rating"),
    [
        ("demagog", "Częściowa prawda"),
        ("demagog", "Manipulacja"),
        ("afp", "Brak kontekstu"),
        ("fakenews-pl", "Częściowy fałsz"),
    ],
)
def test_partial_rating_in_the_table_is_a_context_premise(
    publisher_id: str, rating: str
) -> None:
    rated = rate_review(found(rating, publisher_id), cache_control="max-age=60")
    assert isinstance(rated.evidence, ClaimReviewPremise)
    assert rated.evidence.stance == "context"
    assert rated.evidence.rating == rating


def test_partial_rating_alone_gives_misleading_its_strength() -> None:
    premise = rate_review(found("Częściowa prawda"), cache_control="max-age=60")
    assert isinstance(premise.evidence, ClaimReviewPremise)
    strength = compute_strength(
        "misleading", [], claim_date=CLAIM_DATE, reviews=[premise.evidence]
    )
    assert strength is not None
    assert strength.premises.signatory_reviews == 1


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
