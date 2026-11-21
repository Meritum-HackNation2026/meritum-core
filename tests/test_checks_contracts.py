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
STALE: dict[str, Any] = {
    "level": "moderate",
    "premises": PREMISES | {"newest_source_age_hours": 900 * 24},
}
SHORT_LIVED: dict[str, Any] = {
    "level": "moderate",
    "premises": PREMISES | {"newest_source_age_hours": 48, "max_age_hours": 24},
}
CATALOG: dict[str, Any] = EXAMPLES["CatalogEntry"]


def with_claim(**changes: object) -> dict[str, object]:
    return DONE | {"claims": [CLAIM | changes]}


def result(**changes: object) -> Callable[[], object]:
    return lambda: c.CheckResult.model_validate(with_claim(**changes))


def lasting(validity: str) -> dict[str, object]:
    return {"level": "moderate", "premises": STALE["premises"] | {"validity": validity}}


MUST_REJECT: dict[str, Callable[[], object]] = {
    "settling verdict without citations": result(citations=[]),
    "'confirmed' backed only by a refuting citation": result(verdict="confirmed"),
    "strength that does not follow the premises": result(
        strength={"level": "strong", "premises": PREMISES}
    ),
    "insufficient evidence without saying what is missing": result(
        verdict="insufficient_evidence", unresolved=None
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
            "level": "moderate",
            "premises": PREMISES | {"independent_sources": 2},
        },
    ),
    "stale evidence not marked archival": result(strength=STALE),
    "short-lived evidence older than its catalogue threshold not marked archival": result(
        strength=SHORT_LIVED
    ),
    **{
        f"{v} evidence marked archival": result(strength=lasting(v), archival=True)
        for v in ("in_force", "updated_in_place", "past_event")
    },
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
    "stale evidence marked archival": result(strength=STALE, archival=True),
    **{
        f"{v} evidence is never stale": result(strength=lasting(v))
        for v in ("in_force", "updated_in_place", "past_event")
    },
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


def test_strength_follows_premises() -> None:
    strong = c.Premises.model_validate(
        PREMISES | {"independent_sources": 2, "primary_sources": 1}
    )
    assert c.strength_for(strong) in {"strong", "moderate"}
