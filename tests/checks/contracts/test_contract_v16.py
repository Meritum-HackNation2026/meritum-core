"""Contract v16: CheckResult and CachedResult carry the masked image text (core#128).

Features:
    US-SPR-08, F-33, ADR-02
"""

import pytest
from pydantic import ValidationError

from meritum_core.checks import contracts as c

TEXT = "Sejm przyjął ustawę"


def test_image_text_defaults_to_none() -> None:
    assert (
        c.CheckResult(
            check_id="c1",
            status="needs_clarification",
            message="Podaj treść.",
            corpus_version="v1",
        ).image_text
        is None
    )


def test_result_carries_image_text() -> None:
    result = c.CheckResult(
        check_id="c1",
        status="needs_clarification",
        message="Podaj treść.",
        corpus_version="v1",
        image_text=TEXT,
    )
    assert result.image_text == TEXT


def test_cached_result_carries_image_text() -> None:
    assert "image_text" in c.CachedResult.model_fields


def test_image_text_is_bounded() -> None:
    with pytest.raises(ValidationError):
        c.CheckResult(
            check_id="c1",
            status="needs_clarification",
            message="Podaj treść.",
            corpus_version="v1",
            image_text="x" * 4001,
        )
