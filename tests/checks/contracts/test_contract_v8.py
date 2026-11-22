"""Contract v8: an out_of_scope result names what is not handled.

Features:
    US-SPR-06, F-18
"""

from typing import Any, get_args

import pytest
from pydantic import ValidationError
from tests.checks.contracts.samples import DONE, EXAMPLES

from meritum_core.checks import contracts as c

IMAGE: dict[str, Any] = EXAMPLES["CheckResult.out_of_scope_image"]
CACHED: dict[str, Any] = EXAMPLES["CachedResult"]


def test_code_list_is_closed() -> None:
    assert get_args(c.OutOfScopeCode) == ("image", "audio", "not_informational")


def test_out_of_scope_result_carries_the_code() -> None:
    result = c.CheckResult.model_validate(IMAGE)
    assert result.out_of_scope_code == "image"


def test_rejected_recording_has_one_audio_code_and_the_detail_in_limitations() -> None:
    result = c.CheckResult.model_validate(EXAMPLES["CheckResult.audio_rejected"])
    assert result.out_of_scope_code == "audio"
    assert result.limitation_codes == ["audio_format_unsupported"]


def test_code_is_optional_on_out_of_scope() -> None:
    result = c.CheckResult.model_validate(IMAGE | {"out_of_scope_code": None})
    assert result.out_of_scope_code is None


def test_code_is_empty_on_done() -> None:
    assert c.CheckResult.model_validate(DONE).out_of_scope_code is None


@pytest.mark.parametrize(
    "payload",
    [
        DONE | {"out_of_scope_code": "image"},
        IMAGE | {"status": "needs_clarification"},
        EXAMPLES["CheckResult.failure"] | {"out_of_scope_code": "audio"},
    ],
)
def test_code_is_rejected_on_other_statuses(payload: dict[str, Any]) -> None:
    with pytest.raises(ValidationError, match="only an out_of_scope result"):
        c.CheckResult.model_validate(payload)


def test_unknown_code_is_rejected() -> None:
    with pytest.raises(ValidationError):
        c.CheckResult.model_validate(IMAGE | {"out_of_scope_code": "video"})


def test_cache_keeps_the_code_only_for_out_of_scope() -> None:
    cached = CACHED | {"status": "out_of_scope", "claims": [], "source_ids": []}
    kept = c.CachedResult.model_validate(cached | {"out_of_scope_code": "image"})
    assert kept.out_of_scope_code == "image"
    with pytest.raises(ValidationError, match="only an out_of_scope result"):
        c.CachedResult.model_validate(CACHED | {"out_of_scope_code": "image"})


def test_schema_describes_the_code() -> None:
    for model in (c.CheckResult, c.CachedResult):
        prop = model.model_json_schema()["properties"]["out_of_scope_code"]
        assert "out_of_scope only" in prop["description"]
