"""Contract v6: a finished result carries the machine-readable AI marker (US-BEZ-07)."""

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError
from tests.checks.contracts.samples import EXAMPLES

from meritum_core.checks import contracts as c

AT = datetime(2026, 11, 21, 12, 0, tzinfo=UTC)


def usage(provider: str, model: str) -> c.ModelUsage:
    return c.ModelUsage(
        provider=provider,
        model=model,
        region="europe-central2",
        input_tokens=10,
        output_tokens=5,
        cost_usd=0.0,
    )


@pytest.mark.parametrize(
    ("provider", "model"),
    [("vertex", "gemini-2.0-flash-001"), ("stub", "stub")],
)
def test_marker_names_the_model_that_wrote_the_justification(
    provider: str, model: str
) -> None:
    marker = c.ai_marker_for(usage(provider, model), AT)
    assert marker.model_dump(mode="json") == {
        "ai_generated": True,
        "provider": provider,
        "model": model,
        "generated_at": "2026-11-21T12:00:00Z",
    }


def test_finished_result_carries_the_marker_in_its_json() -> None:
    result = c.CheckResult.model_validate(EXAMPLES["CheckResult.done"])
    dumped = result.model_dump(mode="json")
    assert dumped["ai_marker"]["ai_generated"] is True
    assert dumped["ai_marker"]["model"]


@pytest.mark.parametrize("model", [c.CheckResult, c.CachedResult])
def test_finished_result_without_marker_is_rejected(
    model: type[c.CheckResult | c.CachedResult],
) -> None:
    key = "CheckResult.done" if model is c.CheckResult else "CachedResult"
    data = {k: v for k, v in EXAMPLES[key].items() if k != "ai_marker"}
    with pytest.raises(ValidationError, match="AI marker"):
        model.model_validate(data)


def test_failure_needs_no_marker() -> None:
    result = c.CheckResult.model_validate(EXAMPLES["CheckResult.failure"])
    assert result.ai_marker is None


def test_marker_is_never_false() -> None:
    marker = c.ai_marker_for(usage("stub", "stub"), AT).model_dump()
    with pytest.raises(ValidationError):
        c.AiMarker.model_validate(marker | {"ai_generated": False})
