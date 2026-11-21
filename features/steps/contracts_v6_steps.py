"""Steps for contract v6: a finished result carries the AI marker (US-BEZ-07)."""

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from behave import given, then, when
from behave.runner import Context

from meritum_core.checks.contracts import CheckResult, ModelUsage, ai_marker_for

EXAMPLES: dict[str, Any] = json.loads(
    (Path(__file__).resolve().parents[2] / "contracts" / "examples.json").read_text(
        "utf-8"
    )
)


@given(
    'wynik sprawdzenia z uzasadnieniem napisanym przez model "{model}" '
    'dostawcy "{provider}"'
)
def given_result_written_by_model(context: Context, model: str, provider: str) -> None:
    """A finished result marked by the model call that wrote the justification."""
    context.usage = ModelUsage(
        provider=provider,
        model=model,
        region="europe-central2",
        input_tokens=1200,
        output_tokens=300,
        cost_usd=0.001,
    )
    marker = ai_marker_for(context.usage, datetime.now(UTC))
    context.result = CheckResult.model_validate(
        EXAMPLES["CheckResult.done"] | {"ai_marker": marker.model_dump(mode="json")}
    )


@when("kanał serializuje wynik do odpowiedzi")
def when_channel_serialises(context: Context) -> None:
    """The channel turns the result into JSON, as the API does."""
    context.body = json.loads(context.result.model_dump_json())


@then(
    "odpowiedź ma znacznik czytelny maszynowo z informacją, że uzasadnienie "
    "wygenerował system AI, i z nazwą modelu"
)
def then_body_has_ai_marker(context: Context) -> None:
    """The JSON names AI generation, the provider and the model."""
    marker = context.body["ai_marker"]
    assert marker["ai_generated"] is True
    assert marker["provider"] == context.usage.provider
    assert marker["model"] == context.usage.model
