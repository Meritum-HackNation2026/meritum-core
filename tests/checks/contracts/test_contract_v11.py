"""Contract v11: every limitation text has its code, paired by index.

Features:
    US-SPR-06, US-SPR-11, F-18
"""

from typing import Any

import pytest
from pydantic import ValidationError
from tests.checks.contracts.samples import DONE, EXAMPLES

from meritum_core.checks import contracts as c

CACHED: dict[str, Any] = EXAMPLES["CachedResult"]


def test_corpus_scope_note_has_its_code() -> None:
    result = c.CheckResult.model_validate(DONE)
    assert result.limitation_codes == ["corpus_scope"]
    assert len(result.limitations) == 1


@pytest.mark.parametrize(
    "payload",
    [
        DONE | {"limitation_codes": []},
        DONE | {"limitation_codes": ["corpus_scope", "fact_check_unavailable"]},
        EXAMPLES["CheckResult.audio_rejected"] | {"limitations": []},
    ],
)
def test_texts_and_codes_must_pair(payload: dict[str, Any]) -> None:
    with pytest.raises(ValidationError, match="one code per limitation"):
        c.CheckResult.model_validate(payload)


def test_cached_result_pairs_too() -> None:
    with pytest.raises(ValidationError, match="one code per limitation"):
        c.CachedResult.model_validate(CACHED | {"limitation_codes": []})


def test_schema_says_codes_pair_with_texts() -> None:
    schema = c.CheckResult.model_json_schema()
    description = schema["properties"]["limitation_codes"]["description"]
    assert "Paired with limitations by index" in description
