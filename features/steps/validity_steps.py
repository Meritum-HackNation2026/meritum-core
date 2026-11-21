"""Steps for the evidence age scenarios: claim date, validity and superseded evidence.

The steps call only the public API of meritum_core.evidence.
"""

import json
from datetime import date
from pathlib import Path
from typing import Any

from behave import given, then, when
from behave.runner import Context

from meritum_core.checks.contracts import Citation, is_stale
from meritum_core.evidence import (
    EvidenceFacts,
    assign_validity,
    compute_strength,
    outdated_verdict,
    resolve_claim_date,
)

_TODAY = date(2026, 11, 21)
_EXAMPLES: dict[str, Any] = json.loads(
    (Path(__file__).resolve().parents[2] / "contracts" / "examples.json").read_text(
        "utf-8"
    )
)
_OFFICIAL: dict[str, Any] = _EXAMPLES["CheckResult.done"]["claims"][1]["citations"][0][
    "source"
]


def _cite(stance: str, published_at: str, page: str = "a") -> Citation:
    source = _OFFICIAL | {
        "id": f"kprm-{page}",
        "publisher_id": "kprm",
        "url": f"https://kprm.example.pl/{page}",
        "published_at": published_at,
    }
    return Citation.model_validate(
        {
            "source": source,
            "fragment": f"Komunikat {page} wydawcy (testowy).",
            "stance": stance,
        }
    )


@given("twierdzenie z claim_date {claim_date} pochodzącą z tekstu")
def given_claim_date_from_text(context: Context, claim_date: str) -> None:
    """The claim states its own date."""
    context.claim_date, source = resolve_claim_date(
        date.fromisoformat(claim_date), None, today=_TODAY
    )
    assert source == "text"


@given("najnowszy zgodny dowód opublikowany {published}")
def given_newest_agreeing(context: Context, published: str) -> None:
    """One supporting, expiring piece of evidence published on that day."""
    context.citations = [_cite("supports", f"{published}T00:00:00+02:00")]


@when("system liczy siłę")
def when_strength(context: Context) -> None:
    """Compute strength from the claim date, not from today."""
    context.strength = compute_strength(
        "confirmed", context.citations, claim_date=context.claim_date
    )


@then('siła to "słaba" z przesłanką "dowód nieaktualny"')
def then_weak_and_stale(context: Context) -> None:
    """Weak because the newest source is past the threshold at the claim date."""
    assert context.strength.level == "weak"
    assert is_stale(context.strength.premises)


@given('cytat z pozycji katalogu ISAP o ważności "in_force" sprzed 5 lat')
def given_law_in_force(context: Context) -> None:
    """A five-year-old act from an ISAP entry whose validity is in_force."""
    context.facts = [
        EvidenceFacts(
            citation=_cite("supports", "2021-11-21T00:00:00+01:00"),
            entry_validity="in_force",
        )
    ]


@when("system liczy wiek dowodu")
def when_age(context: Context) -> None:
    """Set validity and compute strength at today's claim date."""
    context.citations = assign_validity(context.facts, claim_date=_TODAY)
    context.strength = compute_strength(
        "confirmed", context.citations, claim_date=_TODAY
    )


@then("cytat nie jest oznaczony jako nieaktualny")
def then_not_stale(context: Context) -> None:
    """Law in force never ages out."""
    assert context.citations[0].validity == "in_force"
    assert not is_stale(context.strength.premises)


@given(
    "starszy dowód wspierający i nowszy urzędowy dowód obalający "
    "od tego samego wydawcy i serii"
)
def given_superseding_pair(context: Context) -> None:
    """An old supporting bulletin and a newer refuting one in the same series."""
    pair = [
        _cite("supports", "2025-03-01T00:00:00+01:00"),
        _cite("refutes", "2026-11-10T00:00:00+01:00", "b"),
    ]
    facts = [EvidenceFacts(citation=c, series="komunikaty") for c in pair]
    context.citations = assign_validity(facts, claim_date=_TODAY)
    context.verdict = "false"


@then('starszy dowód ma ważność "superseded" i nie liczy się do siły ani rozbieżności')
def then_superseded_is_left_out(context: Context) -> None:
    """The older one is superseded: no conflict, only the newer one counts."""
    assert [c.validity for c in context.result.citations] == ["superseded", "expires"]
    premises = context.result.strength.premises
    assert premises.agreement == "consistent"
    assert premises.independent_sources == 1
    assert (
        premises.newest_source_published_at == context.citations[1].source.published_at
    )


@then(
    'werdykt to "fałszywe" albo "wprowadzające w błąd" z techniką "outdated", '
    'nigdy "brak wystarczających dowodów"'
)
def then_outdated_verdict(context: Context) -> None:
    """The verdict settles with the outdated technique."""
    verdict, technique, _ = outdated_verdict(
        context.result.verdict, context.result.citations, claim_date=_TODAY
    )
    assert verdict in {"false", "misleading"}
    assert technique == "outdated"
