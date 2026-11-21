"""Steps for the contract v7 scenarios: codes for a rejected recording.

The When step is shared with the v4 steps (kontrakt waliduje wynik).
"""

import json
from pathlib import Path
from typing import Any

from behave import given, then
from behave.runner import Context

from meritum_core.checks.contracts import CheckResult
from meritum_core.checks.transcription import (
    AudioTooLongError,
    UnsupportedAudioError,
    UnsupportedAudioFormatError,
)

REJECTED: dict[str, Any] = json.loads(
    (Path(__file__).resolve().parents[2] / "contracts" / "examples.json").read_text(
        "utf-8"
    )
)["CheckResult.audio_rejected"]
ERRORS: dict[str, type[UnsupportedAudioError]] = {
    "UnsupportedAudioFormatError": UnsupportedAudioFormatError,
    "AudioTooLongError": AudioTooLongError,
}


@given('wynik "out_of_scope" dla nagrania odrzuconego błędem {error}')
def given_rejected_recording(context: Context, error: str) -> None:
    """An out-of-scope result whose code comes from the transcription error."""
    rejection = ERRORS[error]
    context.model = CheckResult
    context.payload = REJECTED | {"limitation_codes": [rejection.limitation_code]}


@then(
    'wynik ma kod ograniczenia "{code}", z którego kanał wybiera tekst w copy/pl.json'
)
def then_result_has_audio_code(context: Context, code: str) -> None:
    """The rejected recording keeps its status and carries the code."""
    assert context.error is None, context.error
    assert context.validated.status == "out_of_scope"
    assert context.validated.limitation_codes == [code]
