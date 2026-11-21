"""Steps for what would change the verdict (US-ZRD-11), via meritum_core.evidence."""

import json
from datetime import date
from pathlib import Path
from typing import Any

from behave import given, then, when
from behave.runner import Context

from meritum_core.checks.contracts import Citation, ClaimResult, Verdict
from meritum_core.evidence import compute_strength, compute_verdict_changes

EXAMPLES: dict[str, Any] = json.loads(
    (Path(__file__).resolve().parents[2] / "contracts" / "examples.json").read_text(
        "utf-8"
    )
)
CLAIM: dict[str, Any] = EXAMPLES["CheckResult.done"]["claims"][1]
OFFICIAL: dict[str, Any] = CLAIM["citations"][0]["source"]

CLAIM_DATE = date(2026, 11, 21)
GAP = "Urząd i redakcja podają różne liczby dla tego samego dnia."


def _cite(stance: str, publisher_id: str, tier: str) -> Citation:
    source: dict[str, Any] = OFFICIAL | {
        "id": f"{publisher_id}-a",
        "publisher_id": publisher_id,
        "tier": tier,
        "url": f"https://{publisher_id}.example.pl/a",
        "published_at": "2026-11-10T00:00:00+01:00",
    }
    return Citation.model_validate(
        {
            "source": source,
            "fragment": f"Fragment strony wydawcy {publisher_id} (testowy).",
            "stance": stance,
            "validity": "expires",
        }
    )


@given('werdykt "{verdict}" z siłą "{level}" i dwoma zgodnymi wydawcami wtórnymi')
def given_two_secondary_publishers(
    context: Context, verdict: Verdict, level: str
) -> None:
    """Two agreeing secondary publishers; the strength rule must give ``level``."""
    context.verdict = verdict
    context.citations = [
        _cite("supports", "demagog", "secondary"),
        _cite("supports", "oko-press", "secondary"),
    ]
    strength = compute_strength(verdict, context.citations, claim_date=CLAIM_DATE)
    assert strength is not None
    assert strength.level == level


@given('werdykt "{verdict}" ze sprzecznymi cytatami')
def given_conflicting_quotes(context: Context, verdict: Verdict) -> None:
    """A supporting and a refuting citation from different publishers."""
    context.verdict = verdict
    context.citations = [
        _cite("supports", "kancelaria-sejmu", "primary"),
        _cite("refutes", "demagog", "secondary"),
    ]


@when("system liczy, co zmieniłoby werdykt")
def when_changes_are_computed(context: Context) -> None:
    """Compute the codes through the public rule."""
    context.codes = compute_verdict_changes(
        context.verdict, context.citations, claim_date=CLAIM_DATE, unresolved=GAP
    )


@then('wynik ma kod "{code}"')
def then_has_code(context: Context, code: str) -> None:
    """The only code is the expected one."""
    assert context.codes == [code]


@then(
    "wynik ma kod mówiący, że rozstrzygnąłby nowszy dowód urzędowy, "
    "i żadnego faktu spoza wyniku"
)
def then_resolving_code_only(context: Context) -> None:
    """Only a code, never text; the contract accepts it next to both sides."""
    assert context.codes == ["needs_resolving_source"]
    claim = ClaimResult.model_validate(
        CLAIM
        | {
            "verdict": "insufficient_evidence",
            "strength": None,
            "citations": context.citations,
            "unresolved": GAP,
            "would_change_verdict": context.codes,
        }
    )
    assert claim.would_change_verdict == ["needs_resolving_source"]
