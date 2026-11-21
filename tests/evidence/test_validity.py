"""Validity of each piece of evidence, set from metadata at the claim date (ADR-25)."""

from datetime import date

import pytest
from tests.evidence.samples import CLAIM_DATE, cite

from meritum_core.checks.contracts import Citation, Validity
from meritum_core.evidence import EvidenceFacts, assign_validity

OLD = "2025-01-10T00:00:00+01:00"
NEW = "2026-11-10T00:00:00+01:00"


def _validities(
    facts: list[EvidenceFacts], claim_date: date = CLAIM_DATE
) -> list[Validity]:
    return [c.validity for c in assign_validity(facts, claim_date=claim_date)]


@pytest.mark.parametrize(
    ("entry_validity", "past_event", "expected"),
    [
        (None, False, "expires"),
        ("expires", False, "expires"),
        ("in_force", False, "in_force"),
        ("updated_in_place", False, "updated_in_place"),
        ("expires", True, "past_event"),
    ],
)
def test_validity_comes_from_the_catalogue_entry_or_the_event(
    entry_validity: Validity | None, *, past_event: bool, expected: Validity
) -> None:
    facts = EvidenceFacts(
        citation=cite("supports", "kprm", published_at=OLD),
        entry_validity=entry_validity,
        past_event=past_event,
    )
    assert _validities([facts]) == [expected]


def _series(
    old: Citation, new: Citation, series: str | None = "komunikaty"
) -> list[EvidenceFacts]:
    return [
        EvidenceFacts(citation=old, series=series),
        EvidenceFacts(citation=new, series=series),
    ]


def test_older_evidence_of_the_same_publisher_and_series_is_superseded() -> None:
    old = cite("supports", "kprm", published_at=OLD)
    new = cite("refutes", "kprm", published_at=NEW, page="b")
    assert _validities(_series(old, new)) == ["superseded", "expires"]


@pytest.mark.parametrize(
    ("new_publisher", "series", "claim_date"),
    [
        ("gis", "komunikaty", CLAIM_DATE),
        ("kprm", None, CLAIM_DATE),
        ("kprm", "komunikaty", date(2025, 6, 1)),
    ],
    ids=["other-publisher", "no-series", "newer-came-after-the-claim-date"],
)
def test_evidence_is_not_superseded_without_a_newer_one_valid_at_the_claim_date(
    new_publisher: str, series: str | None, claim_date: date
) -> None:
    old = cite("supports", "kprm", published_at=OLD)
    new = cite("refutes", new_publisher, published_at=NEW, page="b")
    assert _validities(_series(old, new, series), claim_date) == ["expires", "expires"]


@pytest.mark.parametrize(
    ("repealed_on", "corrected", "expected"),
    [
        (date(2026, 1, 1), False, "superseded"),
        (date(2026, 12, 1), False, "in_force"),
        (None, True, "superseded"),
    ],
    ids=["repealed-before-claim", "repealed-after-claim", "explicit-correction"],
)
def test_repealed_act_and_corrections_are_superseded_at_the_claim_date(
    repealed_on: date | None, *, corrected: bool, expected: Validity
) -> None:
    facts = EvidenceFacts(
        citation=cite("supports", "isap", published_at=OLD),
        entry_validity="in_force",
        repealed_on=repealed_on,
        corrected=corrected,
    )
    assert _validities([facts]) == [expected]
