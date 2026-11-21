"""Steps for the contract v5 scenario: a check request carries the session id."""

import json
from pathlib import Path
from typing import Any

from behave import given, then, when
from behave.runner import Context

from meritum_core.checks.contracts import CheckRecord, CheckRequest

EXAMPLES: dict[str, Any] = json.loads(
    (Path(__file__).resolve().parents[2] / "contracts" / "examples.json").read_text(
        "utf-8"
    )
)


@given("kanał z identyfikatorem sesji przeglądarki")
def given_browser_session(context: Context) -> None:
    """The extension with a random session id kept in the browser."""
    context.session_id = "s_12345678"


@when("wysyła CheckRequest z polem session_id")
def when_request_has_session_id(context: Context) -> None:
    """The channel sends a check request with the session id."""
    context.request = CheckRequest.model_validate(
        EXAMPLES["CheckRequest"]
        | {"channel": "extension", "session_id": context.session_id}
    )


@then("kontrakt przyjmuje żądanie, a session_id trafia do CheckRecord")
def then_session_id_reaches_record(context: Context) -> None:
    """The request's session id is a valid CheckRecord session id."""
    record = EXAMPLES["CheckRecord"] | {"session_id": context.request.session_id}
    assert CheckRecord.model_validate(record).session_id == context.session_id
