"""Rules from the MSZ brief that the check contracts must enforce.

Ported from design-system/contracts/export_schema.py (the self-check of the
former working copy); the examples live in contracts/examples.json.
"""

import json
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest
from pydantic import TypeAdapter, ValidationError

from meritum_core.checks import contracts as c

EXAMPLES: dict[str, Any] = {
    k: v
    for k, v in json.loads(
        (Path(__file__).parents[1] / "contracts" / "examples.json").read_text("utf-8")
    ).items()
    if not k.startswith("$")
}
ROOTS: dict[str, Any] = {
    "CheckRequest": c.CheckRequest,
    "CheckResult": c.CheckResult,
    "CachedResult": c.CachedResult,
    "AnalysisStatus": c.AnalysisStatus,
    "CheckRecord": c.CheckRecord,
    "ModeratorCase": c.ModeratorCase,
    "CatalogEntry": c.CatalogEntry,
}

DONE: dict[str, Any] = EXAMPLES["CheckResult.done"]
CLAIM: dict[str, Any] = DONE["claims"][0]
PREMISES: dict[str, Any] = CLAIM["strength"]["premises"]
REFUTING: dict[str, Any] = CLAIM["citations"][0]
SUPPORTING = REFUTING | {
    "stance": "supports",
    "fragment": "Prezydent może sprawować urząd przez trzy kadencje (fragment testowy).",
}
SAME_PUBLISHER = REFUTING | {
    "fragment": "Prezydent Rzeczypospolitej jest wybierany przez Naród w wyborach powszechnych."
}
OTHER_SOURCE: dict[str, Any] = REFUTING["source"] | {
    "id": "other-01",
    "publisher": "Inny wydawca",
    "publisher_id": "inny-wydawca",
    "domain": "inny.example.pl",
    "kind": "fact_check",
    "tier": "secondary",
}
SECONDARY_REFUTING = REFUTING | {
    "source": OTHER_SOURCE,
    "fragment": "Ponowny wybór możliwy jest tylko raz (fragment testowy).",
}
CONTEXT_OTHER = SECONDARY_REFUTING | {"stance": "context"}
EXPIRING = REFUTING | {"validity": "expires"}
EXPIRING_PREMISES = PREMISES | {"validity": "expires"}
STALE: dict[str, Any] = {
    "level": "weak",
    "premises": EXPIRING_PREMISES | {"newest_source_age_hours": 900 * 24},
}
SHORT_LIVED: dict[str, Any] = {
    "level": "weak",
    "premises": EXPIRING_PREMISES
    | {"newest_source_age_hours": 48, "max_age_hours": 24},
}
CATALOG: dict[str, Any] = EXAMPLES["CatalogEntry"]
CACHED: dict[str, Any] = EXAMPLES["CachedResult"]
RECORD: dict[str, Any] = EXAMPLES["CheckRecord"]
CASE: dict[str, Any] = EXAMPLES["ModeratorCase"]
HASH = "a" * 64


def with_claim(**changes: object) -> dict[str, object]:
    return DONE | {"claims": [CLAIM | changes]}


def result(**changes: object) -> Callable[[], object]:
    return lambda: c.CheckResult.model_validate(with_claim(**changes))


def stale(**changes: object) -> Callable[[], object]:
    return result(citations=[EXPIRING], **changes)


def lasting(validity: str, **changes: object) -> Callable[[], object]:
    return result(
        citations=[REFUTING | {"validity": validity}],
        strength={
            "level": "moderate",
            "premises": STALE["premises"] | {"validity": validity},
        },
        **changes,
    )


def premises(**changes: object) -> c.Premises:
    return c.Premises.model_validate(EXPIRING_PREMISES | changes)


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
    "cached technical failure": lambda: c.CachedResult.model_validate(
        CACHED | {"status": "technical_failure", "claims": [], "message": "Awaria."}
    ),
    "cache entry that expires before it was stored": lambda: (
        c.CachedResult.model_validate(CACHED | {"expires_at": CACHED["cached_at"]})
    ),
    "cache entry whose source ids are not the cited ones": lambda: (
        c.CachedResult.model_validate(CACHED | {"source_ids": ["x"]})
    ),
    "cache entry carrying an escalation": lambda: c.CachedResult.model_validate(
        CACHED | {"escalation": {"state": "recommended"}}
    ),
    "removed status warning code": lambda: c.SourceStatusWarning.model_validate(
        {
            "code": "state_controlled_media",
            "entity": "X",
            "basis_url": "https://example.org",
        }
    ),
    "injection in user input dropped instead of cut out": lambda: (
        c.InjectionEvent.model_validate(
            {"location": "input", "action": "source_dropped", "excerpt": "Zignoruj."}
        )
    ),
    "injected source kept without its URL": lambda: c.InjectionEvent.model_validate(
        {"location": "source", "action": "source_dropped", "excerpt": "Zignoruj."}
    ),
    "Discord check without a hashed user id": lambda: c.CheckRecord.model_validate(
        RECORD | {"channel": "discord"}
    ),
    "web check with a channel user id": lambda: c.CheckRecord.model_validate(
        RECORD | {"channel_user_hash": HASH}
    ),
    "high-risk case without its topic": lambda: c.ModeratorCase.model_validate(
        CASE | {"high_risk_topic": None}
    ),
    "case listing a reason twice": lambda: c.ModeratorCase.model_validate(
        CASE | {"reasons": ["insufficient_evidence", "insufficient_evidence"]}
    ),
    "catalogue entry that does not expire but has a maximum age": lambda: (
        c.CatalogEntry.model_validate(
            CATALOG | {"validity": "in_force", "max_age_hours": 24}
        )
    ),
    "'past_event' set for a whole catalogue entry": lambda: (
        c.CatalogEntry.model_validate(CATALOG | {"validity": "past_event"})
    ),
    "finished check without limitations": lambda: c.CheckResult.model_validate(
        DONE | {"limitations": []}
    ),
    "technical failure shown with claims": lambda: c.CheckResult.model_validate(
        EXAMPLES["CheckResult.failure"] | {"claims": DONE["claims"]}
    ),
    "recommendation dressed up as a hand-off": lambda: c.Escalation.model_validate(
        {
            "state": "recommended",
            "case_id": "#S-1",
        }
    ),
    "hand-off without a case": lambda: c.Escalation.model_validate(
        {"state": "created"}
    ),
    "request with neither text nor URL": lambda: c.CheckRequest.model_validate(
        {
            "channel": "web",
            "text": "  ",
        }
    ),
    "citation whose fragment was not found": lambda: c.Citation.model_validate(
        REFUTING | {"fragment_found_verbatim": False}
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
    "http URL": lambda: c.CheckRequest.model_validate(
        {"channel": "web", "url": "http://example.gov.pl/komunikat"}
    ),
    "SMS check with a hashed user id": lambda: c.CheckRecord.model_validate(
        RECORD | {"channel": "sms", "channel_user_hash": HASH}
    ),
    "case that is both high-risk and repeated": lambda: c.ModeratorCase.model_validate(
        CASE | {"reasons": ["high_risk", "repeated_unanswered"]}
    ),
    "short-lived catalogue entry": lambda: c.CatalogEntry.model_validate(
        CATALOG | {"domain": "meteo.imgw.pl", "validity": "expires", "max_age_hours": 6}
    ),
}


@pytest.mark.parametrize("name", sorted(EXAMPLES))
def test_examples_are_valid(name: str) -> None:
    TypeAdapter(ROOTS[name.split(".", maxsplit=1)[0]]).validate_python(EXAMPLES[name])


@pytest.mark.parametrize("label", sorted(MUST_REJECT))
def test_rule_rejects(label: str) -> None:
    with pytest.raises(ValidationError):
        MUST_REJECT[label]()


@pytest.mark.parametrize("label", sorted(MUST_ACCEPT))
def test_rule_accepts(label: str) -> None:
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


def test_case_groups_checks_per_claim() -> None:
    case = c.ModeratorCase.model_validate(
        CASE
        | {
            "claims": [
                {"claim": "Pierwsze twierdzenie testowe.", "check_ids": ["c_1", "c_2"]},
                {"claim": "Drugie twierdzenie testowe.", "check_ids": ["c_2", "c_3"]},
            ]
        }
    )
    assert case.check_ids == ["c_1", "c_2", "c_3"]
    assert case.similar_count == 3
