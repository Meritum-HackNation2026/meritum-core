"""Fact-checkers' ClaimReview ratings turned into a premise of the verdict or context.

The rating table in ``constants`` gives a normalized rating its stance per publisher;
a decisive rating of an IFCN or EFCSN signatory becomes a premise that the strength rule
counts as one secondary publisher, anything else stays context with a link. The rating
is never paraphrased, and it is kept no longer than the API's cache headers allow.

Features:
    US-KOR-01, US-ZRD-01, US-ZRD-03, F-14, F-15, ADR-24, ADR-34
"""

import unicodedata
from datetime import timedelta

from meritum_core.checks.contracts import (
    ClaimReviewContext,
    ClaimReviewPremise,
    Stance,
)
from meritum_core.evidence.constants import (
    CLAIM_REVIEW_STANCES,
    MAX_AGE_DIRECTIVE,
    NO_RETENTION_DIRECTIVES,
    RATING_FOLD,
)
from meritum_core.evidence.models import FoundClaimReview, RatedReview


def normalize_rating(rating: str) -> str:
    """Fold a textualRating to the form the rating table is keyed on.

    Args:
        rating: The textualRating as published.

    Returns:
        The rating in lower case, without diacritics, with single spaces.

    Features:
        US-KOR-01, F-14, ADR-34
    """
    decomposed = unicodedata.normalize("NFKD", rating.translate(RATING_FOLD))
    letters = "".join(c for c in decomposed if not unicodedata.combining(c))
    return " ".join(letters.casefold().split())


def rating_stance(publisher_id: str, rating: str) -> Stance:
    """Look up the stance of a fact-checker's rating in its publisher's table.

    Args:
        publisher_id: The catalogue publisher id of the fact-checker.
        rating: The textualRating as published.

    Returns:
        The stance from the table, or ``context`` for a rating or publisher not in it.

    Features:
        US-KOR-01, F-14, ADR-34
    """
    table = CLAIM_REVIEW_STANCES.get(publisher_id)
    stance = table.get(normalize_rating(rating)) if table is not None else None
    return stance or "context"


def rate_review(found: FoundClaimReview, *, cache_control: str | None) -> RatedReview:
    """Turn a found rating into a premise or context, with its retention.

    Args:
        found: The rating as the API returned it, with the catalogue's facts.
        cache_control: The API response's Cache-Control header, when sent.

    Returns:
        A premise for a decisive rating of a signatory, otherwise context with a link;
        either way with the rating verbatim and the end of its retention.

    Features:
        US-KOR-01, US-ZRD-03, F-14, F-15, ADR-24, ADR-34
    """
    stance = rating_stance(found.publisher_id, found.rating)
    is_premise = stance != "context" and bool(found.signatory_of)
    evidence = (
        ClaimReviewPremise.model_validate(found.model_dump() | {"stance": stance})
        if is_premise
        else ClaimReviewContext(
            publisher=found.publisher,
            rating=found.rating,
            url=found.url,
            reviewed_at=found.reviewed_at,
        )
    )
    return RatedReview(
        evidence=evidence,
        keep_until=found.fetched_at + _retention(cache_control),
    )


def _retention(cache_control: str | None) -> timedelta:
    directives = [d.strip().casefold() for d in (cache_control or "").split(",")]
    if NO_RETENTION_DIRECTIVES.intersection(directives):
        return timedelta(0)
    for directive in directives:
        name, _, value = directive.partition("=")
        if name.strip() == MAX_AGE_DIRECTIVE and value.strip().isdigit():
            return timedelta(seconds=int(value))
    # No max-age: the API did not allow keeping the rating at all.
    return timedelta(0)
