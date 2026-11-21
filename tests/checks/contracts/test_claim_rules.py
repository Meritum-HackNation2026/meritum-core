"""Rules from the MSZ brief that a ClaimResult and the strength rule must enforce."""

from collections.abc import Callable

import pytest
from pydantic import ValidationError
from tests.checks.contracts.samples import (
    CONTEXT_OTHER,
    EXPIRING,
    NEWER_CONTEXT,
    NEWER_REFUTING,
    PREMISES,
    REFUTING,
    SAME_PUBLISHER,
    SECONDARY_REFUTING,
    SHORT_LIVED,
    STALE,
    SUPERSEDED_SUPPORTING,
    SUPPORTING,
    lasting,
    premises,
    result,
    stale,
)

from meritum_core.checks import contracts as c

MUST_REJECT: dict[str, Callable[[], object]] = {
    "settling verdict without citations": result(citations=[]),
    "'confirmed' backed only by a refuting citation": result(verdict="confirmed"),
    "strength that does not follow the premises": result(
        strength={"level": "strong", "premises": PREMISES}
    ),
    "insufficient evidence without saying what is missing": result(
        verdict="insufficient_evidence", unresolved=None, citations=[], strength=None
    ),
    "'conflicting' flag the citations do not show": result(
        strength={"level": "weak", "premises": PREMISES | {"agreement": "conflicting"}}
    ),
    "'misleading' without context or technique": result(verdict="misleading"),
    "'confirmed' with a refuting citation next to the supporting one": result(
        verdict="confirmed", citations=[SUPPORTING, REFUTING]
    ),
    "conflicting sources shown with a strength level": result(
        verdict="insufficient_evidence",
        unresolved="Źródła podają różną liczbę kadencji.",
        citations=[SUPPORTING, REFUTING],
    ),
    "insufficient evidence with citations but no conflict": result(
        verdict="insufficient_evidence", unresolved="Brak danych.", strength=None
    ),
    "two pages of one publisher counted as two sources": result(
        citations=[REFUTING, SAME_PUBLISHER],
        strength={
            "level": "strong",
            "premises": PREMISES | {"independent_sources": 2},
        },
    ),
    "stale evidence not marked archival": stale(strength=STALE),
    "short-lived evidence older than its catalogue threshold not marked archival": stale(
        strength=SHORT_LIVED
    ),
    "archival evidence shown as moderate": stale(
        strength=STALE | {"level": "moderate"}, archival=True
    ),
    **{
        f"{v} evidence marked archival": lasting(v, archival=True)
        for v in ("in_force", "updated_in_place", "past_event")
    },
    "non-expiring premises with no citation of that kind": result(citations=[EXPIRING]),
    "publisher whose citation does not agree counted towards strength": result(
        citations=[REFUTING, CONTEXT_OTHER],
        strength={
            "level": "strong",
            "premises": PREMISES | {"independent_sources": 2},
        },
    ),
    "strength on an unsettled verdict": result(
        verdict="not_verifiable", citations=[], unresolved=None
    ),
    "claim date without its origin": result(claim_date_source=None),
    "superseded evidence with no newer evidence next to it": result(
        citations=[SUPERSEDED_SUPPORTING, REFUTING]
    ),
    "superseded evidence counted as a conflict": result(
        verdict="insufficient_evidence",
        unresolved="Brak danych.",
        strength=None,
        citations=[SUPERSEDED_SUPPORTING, NEWER_REFUTING],
    ),
}

MUST_ACCEPT: dict[str, Callable[[], object]] = {
    "conflicting sources: insufficient evidence, both sides, no strength": result(
        verdict="insufficient_evidence",
        unresolved="Źródła podają różną liczbę kadencji.",
        citations=[SUPPORTING, REFUTING],
        strength=None,
    ),
    "two pages of one publisher counted once": result(
        citations=[REFUTING, SAME_PUBLISHER]
    ),
    "stale evidence marked archival and weak": stale(strength=STALE, archival=True),
    **{
        f"{v} evidence is never stale": lasting(v)
        for v in ("in_force", "updated_in_place", "past_event")
    },
    "only the agreeing publisher counts": result(citations=[REFUTING, CONTEXT_OTHER]),
    "two agreeing publishers, one primary: strong": result(
        citations=[REFUTING, SECONDARY_REFUTING],
        strength={
            "level": "strong",
            "premises": PREMISES | {"independent_sources": 2},
        },
    ),
    "older supporting evidence superseded by newer official refutation: false": result(
        citations=[SUPERSEDED_SUPPORTING, NEWER_REFUTING]
    ),
    "superseded evidence: misleading, technique outdated": result(
        verdict="misleading",
        technique="outdated",
        citations=[SUPERSEDED_SUPPORTING, NEWER_CONTEXT],
    ),
    "EUvsDisinfo incident match as context": result(
        incident={
            "database": "euvsdisinfo",
            "incident_id": "eu-1",
            "matched_on": "domain",
            "match_basis": ["domain", "topic"],
            "title": "Przypadek testowy",
            "date": "2025-01-01T00:00:00+01:00",
            "url": "https://euvsdisinfo.eu/report/test/",
            "similarity": 0.9,
        }
    ),
    "fact-check rating shown as context": result(
        claim_reviews=[
            {
                "publisher": "Fact-checker testowy",
                "rating": "Fałsz",
                "url": "https://example.org/fact-check",
            }
        ]
    ),
}


@pytest.mark.parametrize("label", sorted(MUST_REJECT))
def test_claim_rule_rejects(label: str) -> None:
    with pytest.raises(ValidationError):
        MUST_REJECT[label]()


@pytest.mark.parametrize("label", sorted(MUST_ACCEPT))
def test_claim_rule_accepts(label: str) -> None:
    MUST_ACCEPT[label]()


def test_strength_rule() -> None:
    assert (
        c.strength_for(premises(independent_sources=2, primary_sources=1)) == "strong"
    )
    assert (
        c.strength_for(premises(independent_sources=2, primary_sources=0)) == "moderate"
    )
    assert (
        c.strength_for(premises(independent_sources=1, primary_sources=1)) == "moderate"
    )
    assert c.strength_for(premises(independent_sources=1, primary_sources=0)) == "weak"
    assert (
        c.strength_for(
            premises(
                independent_sources=3,
                primary_sources=2,
                newest_source_age_hours=900 * 24,
            )
        )
        == "weak"
    )
