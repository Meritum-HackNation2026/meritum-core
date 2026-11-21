"""Rules from the MSZ brief for the contracts around a claim: request, cache, records."""

from collections.abc import Callable

import pytest
from pydantic import ValidationError
from tests.checks.contracts.samples import (
    CACHED,
    CASE,
    CATALOG,
    DONE,
    EXAMPLES,
    HASH,
    NOTE,
    RECORD,
    REFUTING,
)

from meritum_core.checks import contracts as c

MUST_REJECT: dict[str, Callable[[], object]] = {
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
    "live catalogue entry with a refresh interval": lambda: (
        c.CatalogEntry.model_validate(
            CATALOG | {"ingest": "live", "refresh_minutes": 15}
        )
    ),
    "catalogue entry refreshed more often than every 15 minutes": lambda: (
        c.CatalogEntry.model_validate(CATALOG | {"refresh_minutes": 14})
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
    "live source-status catalogue entry": lambda: c.CatalogEntry.model_validate(
        CATALOG | {"ingest": "live", "role": "source_status"}
    ),
    "short-lived catalogue entry": lambda: c.CatalogEntry.model_validate(
        CATALOG | {"domain": "meteo.imgw.pl", "validity": "expires", "max_age_hours": 6}
    ),
}


@pytest.mark.parametrize("label", sorted(MUST_REJECT))
def test_rule_rejects(label: str) -> None:
    with pytest.raises(ValidationError):
        MUST_REJECT[label]()


@pytest.mark.parametrize("label", sorted(MUST_ACCEPT))
def test_rule_accepts(label: str) -> None:
    MUST_ACCEPT[label]()


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
