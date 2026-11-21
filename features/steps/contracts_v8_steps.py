"""Steps for contract v8: an out_of_scope result names what is not handled.

The When step and "walidacja go odrzuca" are shared with the v4 steps.

Features:
    US-SPR-06, F-18
"""

import json
from pathlib import Path
from typing import Any

from behave import given, then
from behave.runner import Context

from meritum_core.checks.contracts import CheckResult

EXAMPLES: dict[str, Any] = json.loads(
    (Path(__file__).resolve().parents[2] / "contracts" / "examples.json").read_text(
        "utf-8"
    )
)


@given('wynik ze stanem "out_of_scope" dla obrazu')
def given_out_of_scope_image(context: Context) -> None:
    """An out-of-scope result for an image."""
    context.model = CheckResult
    context.payload = EXAMPLES["CheckResult.out_of_scope_image"]


@given('wynik ze stanem "done"')
def given_done_result(context: Context) -> None:
    """A finished check."""
    context.model = CheckResult
    context.payload = EXAMPLES["CheckResult.done"]


@given('wynik ze stanem "done" z kodem powodu "{code}"')
def given_done_with_code(context: Context, code: str) -> None:
    """A finished check that wrongly names an out-of-scope reason."""
    context.model = CheckResult
    context.payload = EXAMPLES["CheckResult.done"] | {"out_of_scope_code": code}
    context.reason = "only an out_of_scope result has an out_of_scope code"


@then('wynik ma kod powodu "{code}", z którego kanał wybiera tekst w copy/pl.json')
def then_result_has_reason(context: Context, code: str) -> None:
    """The out-of-scope result carries its reason code."""
    assert context.error is None, context.error
    assert context.validated.status == "out_of_scope"
    assert context.validated.out_of_scope_code == code


@then("kod powodu jest pusty")
def then_reason_is_empty(context: Context) -> None:
    """A finished check has no out-of-scope reason."""
    assert context.error is None, context.error
    assert context.validated.out_of_scope_code is None
