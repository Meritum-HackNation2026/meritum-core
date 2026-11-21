"""Steps for the evidence strength scenarios: premises and strength from citations.

Citations are built from the example in contracts/examples.json; the steps call only
the public API of meritum_core.evidence.
"""

import json
from collections.abc import Mapping
from datetime import date
from pathlib import Path
from typing import Any

from behave import given, then, when
from behave.runner import Context
from pydantic import ValidationError

from meritum_core.checks.contracts import Citation, ClaimResult
from meritum_core.evidence import compute_premises, compute_strength, settle_verdict

EXAMPLES: dict[str, Any] = json.loads(
    (Path(__file__).resolve().parents[2] / "contracts" / "examples.json").read_text(
        "utf-8"
    )
)
CLAIM: dict[str, Any] = EXAMPLES["CheckResult.done"]["claims"][1]
OFFICIAL: dict[str, Any] = CLAIM["citations"][0]["source"]
CLAIM_DATE = date(2026, 11, 21)
VERDICTS = {
    "potwierdzone": "confirmed",
    "brak wystarczających dowodów": "insufficient_evidence",
}
STRENGTHS = {"mocna": "strong", "umiarkowana": "moderate", "słaba": "weak"}


def _citation(stance: str, publisher_id: str, tier: str, page: str) -> Citation:
    source = OFFICIAL | {
        "id": f"{publisher_id}-{page}",
        "publisher_id": publisher_id,
        "tier": tier,
        "url": f"https://{publisher_id}.example.pl/{page}",
        "published_at": "2026-11-10T00:00:00+01:00",
    }
    return Citation.model_validate(
        {
            "source": source,
            "fragment": f"Fragment strony {page} wydawcy {publisher_id} (testowy).",
            "stance": stance,
            "validity": "expires",
        }
    )


@given('twierdzenie z werdyktem "{verdict}"')
def given_claim_with_verdict(context: Context, verdict: str) -> None:
    """A claim whose proposed verdict is given in Polish."""
    context.verdict = VERDICTS[verdict]


@given(
    "cytaty wspierające od dwóch różnych publisher_id, w tym jednego urzędowego, "
    "oba świeże"
)
def given_two_fresh_publishers(context: Context) -> None:
    """One primary and one secondary supporting citation, both ten days old."""
    context.citations = [
        _citation("supports", "kancelaria-sejmu", "primary", "a"),
        _citation("supports", "demagog", "secondary", "b"),
    ]


@given("dwa cytaty wspierające z różnych stron, ale z tym samym publisher_id")
def given_same_publisher_twice(context: Context) -> None:
    """Two pages of one ministry, both supporting."""
    context.verdict = "confirmed"
    context.citations = [
        _citation("supports", "ministerstwo-zdrowia", "primary", "a"),
        _citation("supports", "ministerstwo-zdrowia", "primary", "b"),
    ]


@given("ważne w dacie twierdzenia cytaty wspierające i obalające od różnych wydawców")
def given_conflicting_citations(context: Context) -> None:
    """A supporting and a refuting citation from different publishers, both current."""
    context.verdict = "confirmed"
    context.citations = [
        _citation("supports", "kancelaria-sejmu", "primary", "a"),
        _citation("refutes", "demagog", "secondary", "b"),
    ]


@when("system liczy przesłanki i siłę")
def when_strength_is_computed(context: Context) -> None:
    """Compute strength through the public rule."""
    context.strength = compute_strength(
        context.verdict, context.citations, claim_date=CLAIM_DATE
    )


@when("system liczy niezależnych wydawców")
def when_publishers_are_counted(context: Context) -> None:
    """Compute the premises through the public rule."""
    context.premises = compute_premises(
        context.verdict, context.citations, claim_date=CLAIM_DATE
    )


@when("system ustala werdykt")
def when_verdict_is_settled(context: Context) -> None:
    """Settle the verdict and build the claim result the contract validates."""
    verdict = settle_verdict(context.verdict, context.citations)
    context.result = ClaimResult.model_validate(
        CLAIM
        | {
            "verdict": verdict,
            "strength": compute_strength(
                verdict, context.citations, claim_date=CLAIM_DATE
            ),
            "citations": context.citations,
            "unresolved": "Urząd i redakcja podają różne liczby dla tego samego dnia.",
        }
    )


@then('siła to "{strength:w}"')
def then_strength_is(context: Context, strength: str) -> None:
    """The computed strength level matches the Polish name."""
    assert context.strength is not None
    assert context.strength.level == STRENGTHS[strength]


@then("liczba niezależnych wydawców wynosi {count:d}")
def then_independent_publishers(context: Context, count: int) -> None:
    """Independence is counted per publisher_id."""
    assert context.premises.independent_sources == count


@then('werdykt to "{verdict}" bez poziomu siły')
def then_verdict_without_strength(context: Context, verdict: str) -> None:
    """Conflicting sources settle nothing and carry no strength."""
    assert context.result.verdict == VERDICTS[verdict]
    assert context.result.strength is None


@then("wynik zawiera cytaty obu stron i notatkę, czym się różnią")
def then_both_sides_and_note(context: Context) -> None:
    """Both stances stay cited next to a note; the contract refuses either missing."""
    result = context.result
    assert {c.stance for c in result.citations} == {"supports", "refutes"}
    assert result.unresolved
    payload = result.model_dump()
    assert _rejected(payload | {"unresolved": None}, "could not be established")
    one_side = payload | {"citations": payload["citations"][:1]}
    assert _rejected(one_side, "only when credible sources conflict")


def _rejected(payload: Mapping[str, object], rule: str) -> bool:
    try:
        ClaimResult.model_validate(payload)
    except ValidationError as error:
        return rule in str(error)
    return False
