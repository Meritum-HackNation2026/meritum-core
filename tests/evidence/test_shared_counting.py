"""Validator and compute_premises count premises with one function (#88)."""

from tests.evidence.samples import CLAIM_DATE, cite, review

from meritum_core.checks.constants import STRONG_MIN_PRIMARY
from meritum_core.checks.contracts import agreeing_evidence, sources_conflict


def test_counts_publishers_per_publisher_id_with_reviews() -> None:
    evidence = agreeing_evidence(
        "confirmed",
        [
            cite("supports", "kprm", "primary"),
            cite("supports", "kprm", "primary", page="b"),
            cite("refutes", "demagog"),
            cite("supports", "old", validity="superseded"),
        ],
        [review("supports", "konkret24"), review("refutes", "oko")],
    )
    assert evidence.publishers == {"kprm", "konkret24"}
    assert evidence.primary == {"kprm"}


def test_non_settling_verdict_agrees_with_nothing() -> None:
    evidence = agreeing_evidence(
        "insufficient_evidence", [cite("supports", "kprm")], []
    )
    assert not evidence.publishers


def test_conflict_ignores_expired_and_superseded_citations() -> None:
    old = cite("refutes", "stary", published_at="2020-01-01T00:00:00+01:00")
    fresh = cite("supports", "nowy")
    assert not sources_conflict([old, fresh], [], CLAIM_DATE)
    assert sources_conflict([old, fresh], [], None)
    assert sources_conflict([fresh], [review("refutes", "oko")], CLAIM_DATE)


def test_primary_threshold_is_a_named_constant() -> None:
    assert STRONG_MIN_PRIMARY == 1
