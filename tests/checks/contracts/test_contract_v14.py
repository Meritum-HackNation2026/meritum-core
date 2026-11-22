"""Contract v14: Source carries its catalogue age threshold (core#120).

Features:
    US-ZRD-05, US-ZRD-10, ADR-02
"""

import pytest
from pydantic import ValidationError
from tests.evidence.samples import SOURCE

from meritum_core.checks import contracts as c


def test_threshold_defaults_to_a_year() -> None:
    source = c.Source.model_validate(SOURCE)
    assert source.max_age_hours is None
    assert c.max_age_for(source) == c.DEFAULT_MAX_AGE_HOURS


def test_catalogue_threshold_wins() -> None:
    source = c.Source.model_validate(SOURCE | {"max_age_hours": 720})
    assert c.max_age_for(source) == 720


def test_threshold_must_be_positive() -> None:
    with pytest.raises(ValidationError):
        c.Source.model_validate(SOURCE | {"max_age_hours": 0})
