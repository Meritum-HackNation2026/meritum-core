"""Premises and strength computed from citations with a stance (ADR-05)."""

from datetime import date

import pytest
from tests.evidence.samples import CLAIM_DATE, cite, review

from meritum_core.checks.contracts import Citation, Stance, Verdict
from meritum_core.evidence import compute_premises, compute_strength, settle_verdict

FRESH = "2026-11-10T00:00:00+01:00"
OLD = "2024-01-01T00:00:00+01:00"
LAW = "1997-07-16T00:00:00+02:00"


@pytest.mark.parametrize(
    ("citations", "level"),
    [
        ([cite("supports", "kprm", "primary"), cite("supports", "demagog")], "strong"),
        ([cite("supports", "demagog"), cite("supports", "oko-press")], "moderate"),
        ([cite("supports", "kprm", "primary")], "moderate"),
        ([cite("supports", "demagog")], "weak"),
        (
            [
                cite("supports", "kprm", "primary", published_at=OLD),
                cite("supports", "demagog", published_at=OLD),
            ],
            "weak",
        ),
    ],
    ids=["strong", "moderate-two", "moderate-primary", "weak-one", "weak-stale"],
)
def test_strength_follows_the_thresholds(citations: list[Citation], level: str) -> None:
    strength = compute_strength("confirmed", citations, claim_date=CLAIM_DATE)
    assert strength is not None
    assert strength.level == level


@pytest.mark.parametrize(
    ("published_at", "level"),
    [("2025-11-21T00:00:00+01:00", "moderate"), ("2025-11-20T23:00:00+01:00", "weak")],
    ids=["exactly-365-days-is-fresh", "one-hour-more-is-stale"],
)
def test_freshness_threshold_is_inclusive(published_at: str, level: str) -> None:
    citation = cite("supports", "kprm", "primary", published_at=published_at)
    strength = compute_strength("confirmed", [citation], claim_date=CLAIM_DATE)
    assert strength is not None
    assert strength.level == level


def test_old_evidence_that_does_not_expire_is_not_stale() -> None:
    law = cite("supports", "kprm", "primary", published_at=OLD, validity="in_force")
    strength = compute_strength("confirmed", [law], claim_date=CLAIM_DATE)
    assert strength is not None
    assert (strength.level, strength.premises.validity) == ("moderate", "in_force")


def test_an_older_expiring_article_does_not_weaken_law_in_force() -> None:
    citations = [
        cite("supports", "kprm", "primary", published_at=LAW, validity="in_force"),
        cite("supports", "demagog", published_at=OLD),
    ]
    strength = compute_strength("confirmed", citations, claim_date=CLAIM_DATE)
    assert strength is not None
    assert (strength.level, strength.premises.validity) == ("strong", "in_force")


def test_pages_of_one_publisher_count_once() -> None:
    pages = [cite("supports", "kprm", "primary", page=p) for p in "ab"]
    premises = compute_premises("confirmed", pages, claim_date=CLAIM_DATE)
    assert (premises.independent_sources, premises.primary_sources) == (1, 1)


@pytest.mark.parametrize(
    ("verdict", "stance"),
    [("confirmed", "supports"), ("false", "refutes"), ("misleading", "context")],
)
def test_only_publishers_agreeing_with_the_verdict_count(
    verdict: Verdict, stance: Stance
) -> None:
    stances: tuple[Stance, ...] = ("supports", "refutes", "context")
    others = [s for s in stances if s != stance]
    citations = [cite(stance, "kprm", "primary")] + [
        cite(s, f"wydawca-{s}") for s in others
    ]
    premises = compute_premises(verdict, citations, claim_date=CLAIM_DATE)
    assert (premises.independent_sources, premises.primary_sources) == (1, 1)


def test_superseded_evidence_neither_counts_nor_conflicts() -> None:
    citations = [
        cite("supports", "demagog"),
        cite("refutes", "kprm", "primary", published_at=OLD, validity="superseded"),
    ]
    assert settle_verdict("confirmed", citations) == "confirmed"
    premises = compute_premises("confirmed", citations, claim_date=CLAIM_DATE)
    assert (premises.independent_sources, premises.agreement) == (1, "consistent")


def test_expired_evidence_does_not_conflict_with_fresh_evidence() -> None:
    citations = [
        cite("supports", "kprm", "primary", published_at=OLD),
        cite("refutes", "demagog"),
    ]
    assert settle_verdict("false", citations, claim_date=CLAIM_DATE) == "false"
    premises = compute_premises("false", citations, claim_date=CLAIM_DATE)
    assert premises.agreement == "consistent"


def test_expired_evidence_conflicts_when_no_claim_date_is_given() -> None:
    citations = [
        cite("supports", "kprm", "primary", published_at=OLD),
        cite("refutes", "demagog"),
    ]
    assert settle_verdict("false", citations) == "insufficient_evidence"


def test_fact_checker_rating_counts_as_a_secondary_publisher() -> None:
    reviews = [review("refutes", "demagog")]
    citations = [cite("refutes", "kprm", "primary")]
    strength = compute_strength(
        "false", citations, claim_date=CLAIM_DATE, reviews=reviews
    )
    assert strength is not None
    assert (strength.premises.independent_sources, strength.level) == (2, "strong")


def test_age_counts_to_the_claim_date_from_the_newest_source() -> None:
    citations = [
        cite("supports", "kprm", "primary", published_at=OLD),
        cite("supports", "demagog", published_at=FRESH),
    ]
    premises = compute_premises("confirmed", citations, claim_date=CLAIM_DATE)
    assert premises.newest_source_published_at is not None
    assert premises.newest_source_published_at.isoformat() == FRESH
    assert premises.newest_source_age_hours == 11 * 24
    assert premises.validity == "expires"


def test_source_newer_than_the_claim_date_has_age_zero() -> None:
    premises = compute_premises(
        "confirmed", [cite("supports", "demagog")], claim_date=date(2026, 1, 1)
    )
    assert premises.newest_source_age_hours == 0


@pytest.mark.parametrize("verdict", ["insufficient_evidence", "not_verifiable"])
def test_only_settling_verdicts_get_a_strength(verdict: Verdict) -> None:
    citations = [cite("supports", "kprm", "primary")]
    assert compute_strength(verdict, citations, claim_date=CLAIM_DATE) is None


def test_conflicting_sources_settle_as_insufficient_evidence_without_strength() -> None:
    citations = [cite("supports", "kprm", "primary"), cite("refutes", "demagog")]
    assert settle_verdict("confirmed", citations) == "insufficient_evidence"
    assert compute_strength("confirmed", citations, claim_date=CLAIM_DATE) is None


def test_a_fact_checker_rating_can_create_the_conflict() -> None:
    citations = [cite("supports", "kprm", "primary")]
    reviews = [review("refutes", "demagog")]
    assert settle_verdict("confirmed", citations, reviews) == "insufficient_evidence"


def test_consistent_sources_keep_the_proposed_verdict() -> None:
    citations = [cite("refutes", "kprm", "primary"), cite("context", "demagog")]
    assert settle_verdict("false", citations) == "false"


def test_catalogue_threshold_shorter_than_a_year_makes_evidence_stale() -> None:
    citation = cite(
        "supports", "imgw", "primary", published_at="2026-11-17T00:00:00+01:00"
    )
    strength = compute_strength(
        "confirmed", [citation], claim_date=CLAIM_DATE, max_age_hours=48
    )
    assert strength is not None
    assert strength.level == "weak"
