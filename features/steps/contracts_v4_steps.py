"""Steps for the contract v4 scenarios, with payloads from contracts/examples.json.

The When steps validate it through the public contract and keep the error, if any.
"""

import json
from pathlib import Path
from typing import Any

from behave import given, then, when
from behave.runner import Context
from pydantic import ValidationError

from meritum_core.checks.contracts import CheckRequest, CheckResult

EXAMPLES: dict[str, Any] = json.loads(
    (Path(__file__).resolve().parents[2] / "contracts" / "examples.json").read_text(
        "utf-8"
    )
)
DONE: dict[str, Any] = EXAMPLES["CheckResult.done"]
CLAIM: dict[str, Any] = DONE["claims"][0]
INCIDENT: dict[str, Any] = {
    "database": "fact_check",
    "incident_id": "demagog-1",
    "matched_on": "content",
    "match_basis": ["domain"],
    "title": "Trzecia kadencja prezydenta",
    "date": "2026-11-01T00:00:00+01:00",
    "url": "https://demagog.org.pl/wypowiedzi/test/",
    "similarity": 0.9,
}


def _done_with_claim(**changes: object) -> dict[str, Any]:
    return DONE | {"claims": [CLAIM | changes]}


@given("żądanie z channel = web i identyfikatorem użytkownika kanału")
def given_web_request_with_user_id(context: Context) -> None:
    """A browser-channel request that still carries a channel user id."""
    context.model = CheckRequest
    context.payload = EXAMPLES["CheckRequest"] | {"channel_user_id": "123456789"}


@given(
    "sprawdzenie zakończone stanem done, "
    "a Google Fact Check Tools API zwróciło błąd dostępu"
)
def given_done_without_fact_checks(context: Context) -> None:
    """A finished check whose fact-check index lookup failed."""
    context.model = CheckResult
    context.payload = DONE | {"limitation_codes": ["fact_check_unavailable"]}


@given(
    'ClaimResult z werdyktem "fałszywe" i jedyną przesłanką z ClaimReview Demagogu '
    'z textualRating "Fałsz", tytułem, datą i linkiem'
)
def given_claim_review_premise(context: Context) -> None:
    """A false verdict whose only premise is the Demagog ClaimReview."""
    context.model = CheckResult
    context.payload = EXAMPLES["CheckResult.claim_review"]


@given(
    "IncidentMatch z podstawą dopasowania zawierającą tylko domenę "
    'i matched_on "content"'
)
def given_domain_only_content_match(context: Context) -> None:
    """A content match whose only basis is the domain."""
    context.model = CheckResult
    context.payload = _done_with_claim(incident=INCIDENT)


@given('wynik "done" z twierdzeniem bez claim_date')
def given_claim_without_date(context: Context) -> None:
    """A finished check with a claim that has no claim date."""
    context.model = CheckResult
    claim = {k: v for k, v in CLAIM.items() if k != "claim_date"}
    context.payload = DONE | {"claims": [claim]}


@when("kontrakt waliduje żądanie")
@when("kontrakt waliduje wynik")
@when("kontrakt waliduje twierdzenie")
@when("worker składa CheckResult")
def when_contract_validates(context: Context) -> None:
    """Validate the payload; keep the model or the validation error."""
    context.error = None
    try:
        context.validated = context.model.model_validate(context.payload)
    except ValidationError as error:
        context.error = error


@then("walidacja je odrzuca")
@then("walidacja go odrzuca")
@then(
    "walidacja je odrzuca, bo dopasowanie treści wymaga zgodnego tytułu, tematu i daty"
)
def then_validation_rejects(context: Context) -> None:
    """The contract refused the payload."""
    assert context.error is not None


@then("walidacja go przyjmuje, choć przesłanka nie ma fragmentu strony")
def then_validation_accepts(context: Context) -> None:
    """The contract took the payload as it is."""
    assert context.error is None, context.error


@then(
    'wynik ma kod ograniczenia "{code}", '
    "z którego kanał składa komunikat o błędzie dostępu do indeksu"
)
def then_result_has_limitation_code(context: Context, code: str) -> None:
    """The finished result carries the limitation code for the channel's copy."""
    assert context.error is None, context.error
    assert code in context.validated.limitation_codes


@then("stan sprawdzenia nie jest technical_failure")
def then_status_is_not_failure(context: Context) -> None:
    """A limitation does not turn the check into a technical failure."""
    assert context.validated.status != "technical_failure"
