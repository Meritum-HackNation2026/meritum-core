"""Steps for the ClaimReview scenarios: a rating as a premise or as context."""

import json
from datetime import date
from pathlib import Path
from typing import Any

from behave import given, then, when
from behave.runner import Context

from meritum_core.checks.contracts import ClaimReviewContext, ClaimReviewPremise
from meritum_core.evidence import (
    FoundClaimReview,
    compute_strength,
    rate_review,
    settle_verdict,
)

_EXAMPLES: dict[str, Any] = json.loads(
    (Path(__file__).resolve().parents[2] / "contracts" / "examples.json").read_text(
        "utf-8"
    )
)
_REVIEW: dict[str, Any] = _EXAMPLES["CheckResult.claim_review"]["claims"][0][
    "claim_review_premises"
][0]
_CLAIM_DATE = date(2026, 11, 21)
_CACHE_CONTROL = "max-age=86400"


def _found(rating: str) -> FoundClaimReview:
    fields = {k: v for k, v in _REVIEW.items() if k != "stance"}
    return FoundClaimReview.model_validate(fields | {"rating": rating})


@given('twierdzenie "{claim}"')
def given_claim(context: Context, claim: str) -> None:
    """The claim under check."""
    context.claim = claim


@given('ClaimReview od Demagogu z textualRating "{rating}", tytułem, datą i linkiem')
@given('ClaimReview z textualRating "{rating}"')
def given_claim_review(context: Context, rating: str) -> None:
    """Google Fact Check Tools API returned Demagog's rating."""
    context.found_review = _found(rating)


@given("ClaimReview z textualRating, którego nie ma w tabeli mapowania ocen")
def given_unmapped_review(context: Context) -> None:
    """Demagog's rating uses a wording the table does not list."""
    context.found_review = _found("Nie do końca")


@when("system liczy werdykt i przesłanki")
@when("system liczy werdykt")
@when("kanał pokazuje przesłankę")
def when_rating_is_read(context: Context) -> None:
    """The rating becomes a premise or context; the verdict and strength follow."""
    evidence = rate_review(context.found_review, cache_control=_CACHE_CONTROL).evidence
    context.review_evidence = evidence
    reviews = [evidence] if isinstance(evidence, ClaimReviewPremise) else []
    context.verdict = settle_verdict("false", [], reviews)
    context.strength = compute_strength(
        context.verdict, [], claim_date=_CLAIM_DATE, reviews=reviews
    )


@then(
    'werdykt to "fałszywe" z przesłanką z oceną "{rating}", tytułem, datą i linkiem'
    " do Demagogu, bez fragmentu strony"
)
def then_false_with_premise(context: Context, rating: str) -> None:
    """The verdict rests on the rating; the premise carries no page fragment."""
    premise = context.review_evidence
    assert isinstance(premise, ClaimReviewPremise)
    assert context.verdict == "false"
    assert premise.rating == rating
    assert premise.publisher_id == "demagog"
    assert premise.title
    assert premise.reviewed_at
    assert str(premise.url).startswith("https://demagog.org.pl/")
    assert "fragment" not in ClaimReviewPremise.model_fields


@then(
    "siła liczy Demagoga jako jednego niezależnego wydawcę wtórnego,"
    ' więc sama nie jest "mocna"'
)
def then_one_secondary_publisher(context: Context) -> None:
    """One fact-checker is one secondary publisher, never strong on its own."""
    premises = context.strength.premises
    assert premises.independent_sources == 1
    assert premises.primary_sources == 0
    assert context.strength.level != "strong"


@then("ocena zostaje kontekstem z linkiem i nie jest przesłanką")
def then_context_only(context: Context) -> None:
    """An unmapped rating is shown as context and settles nothing."""
    assert isinstance(context.review_evidence, ClaimReviewContext)
    assert context.review_evidence.url
    assert context.strength.premises.independent_sources == 0


@then('ocena ma dokładnie brzmienie "{rating}", a nie parafrazę modelu')
def then_verbatim_rating(context: Context, rating: str) -> None:
    """The rating is shown exactly as the fact-checker published it."""
    assert context.review_evidence.rating == rating


@when("system liczy werdykt „wprowadzające w błąd”")
def when_misleading_is_counted(context: Context) -> None:
    """A context rating backs ``misleading``; its strength is counted."""
    evidence = rate_review(context.found_review, cache_control=_CACHE_CONTROL).evidence
    context.review_evidence = evidence
    reviews = [evidence] if isinstance(evidence, ClaimReviewPremise) else []
    context.strength = compute_strength(
        "misleading", [], claim_date=_CLAIM_DATE, reviews=reviews
    )


@then(
    'ocena jest przesłanką ze stance "context", a werdykt ma siłę z jednej oceny'
    " sygnatariusza"
)
def then_context_premise(context: Context) -> None:
    """The rating is a premise of ``misleading``, counted as one signatory rating."""
    assert isinstance(context.review_evidence, ClaimReviewPremise)
    assert context.review_evidence.stance == "context"
    assert context.strength is not None
    assert context.strength.premises.signatory_reviews == 1
