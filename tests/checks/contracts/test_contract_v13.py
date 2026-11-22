"""Contract v13: AnalysisStatus carries a streamed answer draft.

Features:
    US-SPR-02, ADR-02
"""

import pytest
from pydantic import ValidationError

from meritum_core.checks import contracts as c

STEPS = [{"code": "receive", "status": "done"}]


def test_version_is_13() -> None:
    assert c.CONTRACT_VERSION == 13


def test_draft_is_optional() -> None:
    status = c.AnalysisStatus.model_validate({"check_id": "c_01", "steps": STEPS})
    assert status.draft is None


def test_draft_carries_the_streamed_text() -> None:
    status = c.AnalysisStatus.model_validate(
        {"check_id": "c_01", "steps": STEPS, "draft": "Wstępnie: nie znaleziono"}
    )
    assert status.draft == "Wstępnie: nie znaleziono"


def test_draft_is_capped() -> None:
    with pytest.raises(ValidationError):
        c.AnalysisStatus.model_validate(
            {"check_id": "c_01", "steps": STEPS, "draft": "x" * 4001}
        )
