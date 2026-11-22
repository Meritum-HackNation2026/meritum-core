"""Steps for expired evidence next to a fresh refutation (US-ZRD-10, core#110).

The steps call only the public API of meritum_core.evidence and the contracts.
"""

import json
from datetime import date
from pathlib import Path
from typing import Any

from behave import given, then, when
from behave.runner import Context

from meritum_core.checks.contracts import Citation, ClaimResult
from meritum_core.evidence import (
    EvidenceFacts,
    assign_validity,
    compute_strength,
    settle_verdict,
)

_CLAIM_DATE = date(2026, 11, 21)
_CLAIM: dict[str, Any] = json.loads(
    (Path(__file__).resolve().parents[2] / "contracts" / "examples.json").read_text(
        "utf-8"
    )
)["CheckResult.done"]["claims"][0]


def _cite(
    stance: str, publisher_id: str, published_at: str, max_age_hours: int | None = None
) -> Citation:
    source = _CLAIM["citations"][0]["source"] | {
        "max_age_hours": max_age_hours,
        "id": f"{publisher_id}-a",
        "publisher_id": publisher_id,
        "url": f"https://{publisher_id}.example.pl/a",
        "published_at": published_at,
    }
    return Citation.model_validate(
        {"source": source, "fragment": "Fragment (testowy).", "stance": stance}
    )


@given("dowód z expires starszy niż data twierdzenia i świeże obalenie")
def given_expired_and_fresh(context: Context) -> None:
    """A 2020 expiring article supports; a fresh one from another publisher refutes."""
    facts = [
        EvidenceFacts(citation=_cite("supports", "kprm", "2020-01-01T00:00:00+01:00")),
        EvidenceFacts(
            citation=_cite("refutes", "demagog", "2026-11-10T00:00:00+01:00")
        ),
    ]
    context.citations = assign_validity(facts, claim_date=_CLAIM_DATE)


@when("system ustala werdykt z datą twierdzenia")
def when_settle_at_claim_date(context: Context) -> None:
    """Settle the proposed verdict and its strength at the claim date."""
    verdict = settle_verdict("false", context.citations, claim_date=_CLAIM_DATE)
    strength = compute_strength(verdict, context.citations, claim_date=_CLAIM_DATE)
    context.verdict, context.strength = verdict, strength
    if verdict == "insufficient_evidence":
        return  # a conflict: the explanation is the channel's job, not this rule's
    context.claim = ClaimResult.model_validate(
        _CLAIM
        | {
            "claim_date": _CLAIM_DATE,
            "verdict": verdict,
            "strength": strength,
            "citations": context.citations,
        }
    )


@then("werdykt opiera się na świeżym dowodzie")
def then_fresh_evidence_settles(context: Context) -> None:
    """No conflict: the fresh refutation settles the claim and is the only premise."""
    assert context.claim.verdict == "false"
    premises = context.claim.strength.premises
    assert premises.agreement == "consistent"
    assert premises.independent_sources == 1
    assert premises.newest_source_age_hours == 11 * 24


@given("źródło z katalogu z max_age_hours = 720")
def given_catalogue_threshold(context: Context) -> None:
    """The source's catalogue entry allows 30 days."""
    context.max_age_hours = 720


@given("źródło bez max_age_hours")
def given_no_catalogue_threshold(context: Context) -> None:
    """The source carries no catalogue threshold."""
    context.max_age_hours = None


@given("dowód tego źródła starszy o 40 dni od daty twierdzenia obok świeżego obalenia")
def given_forty_days_old_and_fresh(context: Context) -> None:
    """A 40-day-old support from that source next to a fresh refutation."""
    facts = [
        EvidenceFacts(
            citation=_cite(
                "supports", "kprm", "2026-10-12T00:00:00+01:00", context.max_age_hours
            )
        ),
        EvidenceFacts(
            citation=_cite("refutes", "demagog", "2026-11-10T00:00:00+01:00")
        ),
    ]
    context.citations = assign_validity(facts, claim_date=_CLAIM_DATE)


@then("ten dowód jest przeterminowany i nie tworzy rozbieżności")
def then_expired_by_catalogue(context: Context) -> None:
    """The catalogue threshold expires the support, so the refutation settles."""
    assert context.claim.verdict == "false"
    assert context.claim.strength.premises.agreement == "consistent"


@then("działa domyślny próg 365 dni")
def then_default_threshold(context: Context) -> None:
    """Within 365 days the support still conflicts with the refutation."""
    assert context.verdict == "insufficient_evidence"
    assert context.strength is None
