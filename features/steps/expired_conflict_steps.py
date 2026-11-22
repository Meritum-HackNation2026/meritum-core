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


def _cite(stance: str, publisher_id: str, published_at: str) -> Citation:
    source = _CLAIM["citations"][0]["source"] | {
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
