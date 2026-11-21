"""Contract v7: a rejected recording carries its own limitation code (US-SPR-11)."""

from typing import get_args

import pytest
from tests.checks.contracts.samples import EXAMPLES

from meritum_core.checks import contracts as c
from meritum_core.checks.transcription import (
    AudioTooLongError,
    UnsupportedAudioError,
    UnsupportedAudioFormatError,
)


@pytest.mark.parametrize(
    ("error", "code"),
    [
        (UnsupportedAudioFormatError, "audio_format_unsupported"),
        (AudioTooLongError, "audio_too_long"),
    ],
)
def test_rejected_recording_names_its_limitation_code(
    error: type[UnsupportedAudioError], code: str
) -> None:
    assert error.limitation_code == code
    assert code in get_args(c.LimitationCode)


def test_out_of_scope_audio_result_carries_the_code() -> None:
    result = c.CheckResult.model_validate(EXAMPLES["CheckResult.audio_rejected"])
    assert result.status == "out_of_scope"
    assert result.limitation_codes == ["audio_format_unsupported"]


def test_schema_says_codes_and_texts_are_not_paired() -> None:
    schema = c.CheckResult.model_json_schema()
    description = schema["properties"]["limitation_codes"]["description"]
    assert "Not paired with limitations by index" in description


def test_contract_version_is_7() -> None:
    assert c.CONTRACT_VERSION == 7
