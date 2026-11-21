"""Claim date and the verdict on evidence that was true once (US-ZRD-05, US-ZRD-10)."""

from datetime import date, datetime, timedelta, timezone

import pytest
from tests.evidence.samples import CLAIM_DATE, cite

from meritum_core.evidence import outdated_verdict, resolve_claim_date

TODAY = date(2026, 11, 21)
PUBLISHED = datetime(2026, 11, 2, 23, 30, tzinfo=timezone(timedelta(hours=1)))


@pytest.mark.parametrize(
    ("text_date", "published_at", "expected"),
    [
        (date(2026, 11, 1), PUBLISHED, (date(2026, 11, 1), "text")),
        (None, PUBLISHED, (date(2026, 11, 2), "input_published_at")),
        (None, None, (TODAY, "today")),
    ],
    ids=["text", "input-published-at", "today"],
)
def test_claim_date_prefers_the_text_then_the_input_then_today(
    text_date: date | None, published_at: datetime | None, expected: tuple[date, str]
) -> None:
    assert resolve_claim_date(text_date, published_at, today=TODAY) == expected


def test_superseded_supporting_evidence_makes_the_claim_outdated_not_insufficient() -> (
    None
):
    citations = [
        cite(
            "supports",
            "kprm",
            published_at="2025-01-10T00:00:00+01:00",
            validity="superseded",
        ),
        cite("refutes", "kprm", "primary", page="b"),
    ]
    assert outdated_verdict("false", citations, claim_date=CLAIM_DATE) == (
        "false",
        "outdated",
        False,
    )


def test_present_tense_claim_backed_only_by_stale_evidence_is_misleading_and_archival() -> (
    None
):
    citations = [
        cite("supports", "kprm", "primary", published_at="2024-01-01T00:00:00+01:00")
    ]
    assert outdated_verdict(
        "confirmed", citations, claim_date=CLAIM_DATE, present_tense=True
    ) == ("misleading", "outdated", True)


@pytest.mark.parametrize("present_tense", [True, False])
def test_fresh_evidence_keeps_the_verdict(*, present_tense: bool) -> None:
    citations = [cite("supports", "kprm", "primary")]
    assert outdated_verdict(
        "confirmed", citations, claim_date=CLAIM_DATE, present_tense=present_tense
    ) == ("confirmed", None, False)


def test_past_dated_claim_with_evidence_valid_then_keeps_the_verdict() -> None:
    citations = [
        cite("supports", "kprm", "primary", published_at="2024-01-01T00:00:00+01:00")
    ]
    assert outdated_verdict("confirmed", citations, claim_date=date(2024, 3, 1)) == (
        "confirmed",
        None,
        False,
    )


def test_a_superseded_refutation_next_to_a_current_one_is_not_outdated() -> None:
    citations = [
        cite(
            "refutes",
            "kprm",
            published_at="2025-01-10T00:00:00+01:00",
            validity="superseded",
        ),
        cite("refutes", "kprm", "primary", page="b"),
    ]
    assert outdated_verdict("false", citations, claim_date=CLAIM_DATE) == (
        "false",
        None,
        False,
    )
