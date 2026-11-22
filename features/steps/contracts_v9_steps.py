"""Steps for contract v9: a notification carries step and system message codes.

"walidacja go odrzuca" is shared with the v4 steps.

Features:
    US-POW-01, US-POW-04, F-26
"""

import json
from pathlib import Path
from typing import Any, get_args

from behave import given, then, when
from behave.runner import Context
from pydantic import ValidationError

from meritum_core.checks.contracts import Notification, SystemMessageCode

EXAMPLES: dict[str, Any] = json.loads(
    (Path(__file__).resolve().parents[2] / "contracts" / "examples.json").read_text(
        "utf-8"
    )
)


@given('workflow sprawdzania kończy krok "{code}"')
def given_finished_step(context: Context, code: str) -> None:
    """The check workflow finished a pipeline step."""
    context.payload = EXAMPLES["Notification.check_progress"] | {"step_code": code}


@given('zespół wysyła informację systemową "{code}"')
def given_system_message(context: Context, code: str) -> None:
    """The team sends a system message by its code."""
    context.payload = EXAMPLES["Notification.system"] | {"message_code": code}


@given("workflow sprawdzania nie podaje kodu kroku")
def given_progress_without_step(context: Context) -> None:
    """A progress notification that names no step."""
    payload = dict(EXAMPLES["Notification.check_progress"])
    del payload["step_code"]
    context.payload = payload
    context.reason = "'check_progress' names a step"


@when('powstaje Notification z kind "{kind}"')
def when_notification_is_built(context: Context, kind: str) -> None:
    """Validate the notification; keep the model or the validation error."""
    context.error = None
    try:
        context.validated = Notification.model_validate(
            context.payload | {"kind": kind}
        )
    except ValidationError as error:
        context.error = error


@then(
    'powiadomienie niesie kod kroku "{code}", '
    "a aplikacja pokazuje tekst kroku z copy/pl.json"
)
def then_carries_step(context: Context, code: str) -> None:
    """The progress notification carries the step code and no message code."""
    assert context.error is None, context.error
    assert context.validated.step_code == code
    assert context.validated.message_code is None


@then('powiadomienie niesie kod komunikatu "{code}" z copy/pl.json, nie wolny tekst')
def then_carries_message(context: Context, code: str) -> None:
    """The system notification carries a code from the closed list, not text."""
    assert context.error is None, context.error
    assert context.validated.message_code == code
    assert context.validated.message_code in get_args(SystemMessageCode)
