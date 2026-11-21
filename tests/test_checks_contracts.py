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
    "Notification": c.Notification,
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
NOTE: dict[str, Any] = EXAMPLES["Notification"]
HASH = "a" * 64
SUPERSEDED_SUPPORTING = SUPPORTING | {"validity": "superseded"}
NEWER_SOURCE: dict[str, Any] = REFUTING["source"] | {
    "id": "isap-newer",
    "published_at": "2025-01-01T00:00:00+01:00",
}
NEWER_REFUTING = REFUTING | {
    "source": NEWER_SOURCE,
    "fragment": "Nowszy dokument urzędowy obala to twierdzenie (fragment testowy).",
}
NEWER_CONTEXT = NEWER_REFUTING | {"stance": "context"}


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
    "superseded evidence with no newer evidence next to it": result(
        citations=[SUPERSEDED_SUPPORTING, REFUTING]
    ),
    "superseded evidence counted as a conflict": result(
        verdict="insufficient_evidence",
        unresolved="Brak danych.",
        strength=None,
        citations=[SUPERSEDED_SUPPORTING, NEWER_REFUTING],
    ),
    "'superseded' set for a whole catalogue entry": lambda: (
        c.CatalogEntry.model_validate(CATALOG | {"validity": "superseded"})
    ),
    "secondary source kept although it reserved text and data mining": lambda: (
        c.CatalogEntry.model_validate(
            EXAMPLES["CatalogEntry.euvsdisinfo"] | {"tdm_reservation": "reserved"}
        )
    ),
    "MCP check without a hashed user id": lambda: c.CheckRecord.model_validate(
        RECORD | {"channel": "mcp"}
    ),
    "Discord check whose session id is not the hashed user id": lambda: (
        c.CheckRecord.model_validate(
            RECORD | {"channel": "discord", "channel_user_hash": HASH}
        )
    ),
    "notification to both a session and a user": lambda: c.Notification.model_validate(
        NOTE | {"user_id": "u_12345678"}
    ),
    "notification to nobody": lambda: c.Notification.model_validate(
        NOTE | {"session_id": None}
    ),
    "finished-check notification without the check": lambda: (
        c.Notification.model_validate(NOTE | {"check_id": None})
    ),
    "moderator answer without the case": lambda: c.Notification.model_validate(
        NOTE | {"kind": "moderator_answer"}
    ),
    "notification linking outside the app": lambda: c.Notification.model_validate(
        NOTE | {"link": "https://example.org"}
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
    "SMS check with a hashed user id as its session": lambda: (
        c.CheckRecord.model_validate(
            RECORD | {"channel": "sms", "channel_user_hash": HASH, "session_id": HASH}
        )
    ),
    "MCP check with a hashed client id as its session": lambda: (
        c.CheckRecord.model_validate(
            RECORD | {"channel": "mcp", "channel_user_hash": HASH, "session_id": HASH}
        )
    ),
    "older supporting evidence superseded by newer official refutation: false": result(
        citations=[SUPERSEDED_SUPPORTING, NEWER_REFUTING]
    ),
    "superseded evidence: misleading, technique outdated": result(
        verdict="misleading",
        technique="outdated",
        citations=[SUPERSEDED_SUPPORTING, NEWER_CONTEXT],
    ),
    "audio upload": lambda: c.CheckRequest.model_validate(
        {"channel": "discord", "audio_id": "a_01"}
    ),
    "case opened by a user dispute": lambda: c.ModeratorCase.model_validate(
        CASE
        | {
            "reasons": ["user_dispute"],
            "high_risk_topic": None,
            "high_risk_classified_by": None,
        }
    ),
    "EUvsDisinfo incident match as context": result(
        incident={
            "database": "euvsdisinfo",
            "incident_id": "eu-1",
            "matched_on": "domain",
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
    "case notification for a signed-in moderator": lambda: (
        c.Notification.model_validate(
            NOTE
            | {
                "kind": "case_assigned",
                "session_id": None,
                "user_id": "u_12345678",
                "check_id": None,
                "case_id": "#S-1",
                "link": "/panel/sprawy/S-1",
            }
        )
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
