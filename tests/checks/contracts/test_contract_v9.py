"""Contract v9: a notification carries the progress step and system message codes.

Features:
    US-POW-01, US-POW-04, F-26
"""

from typing import Any, get_args

import pytest
from pydantic import ValidationError
from tests.checks.contracts.samples import EXAMPLES

from meritum_core.checks import contracts as c

PROGRESS: dict[str, Any] = EXAMPLES["Notification.check_progress"]
SYSTEM: dict[str, Any] = EXAMPLES["Notification.system"]
DONE: dict[str, Any] = EXAMPLES["Notification"]


def test_step_codes_are_the_analysis_step_codes() -> None:
    step = c.AnalysisStep.model_json_schema()["properties"]["code"]["enum"]
    assert list(get_args(c.AnalysisStepCode)) == step


def test_message_code_list_is_closed() -> None:
    assert get_args(c.SystemMessageCode) == (
        "maintenance_planned",
        "service_degraded",
        "service_restored",
    )


def test_progress_carries_the_step() -> None:
    assert c.Notification.model_validate(PROGRESS).step_code == "search_corpus"


def test_system_carries_the_message_code() -> None:
    note = c.Notification.model_validate(SYSTEM)
    assert note.message_code == "maintenance_planned"
    assert note.check_id is None


def test_other_kinds_carry_no_codes() -> None:
    note = c.Notification.model_validate(DONE)
    assert (note.step_code, note.message_code) == (None, None)


@pytest.mark.parametrize(
    ("payload", "reason"),
    [
        (PROGRESS | {"step_code": None}, "'check_progress' names a step"),
        (SYSTEM | {"message_code": None}, "'system' names a message code"),
        (DONE | {"step_code": "receive"}, "only 'check_progress' names a step"),
        (DONE | {"message_code": "service_degraded"}, "only 'system' names a message"),
        (PROGRESS | {"message_code": "service_degraded"}, "only 'system' names"),
        (SYSTEM | {"step_code": "receive"}, "only 'check_progress' names a step"),
    ],
)
def test_codes_follow_the_kind(payload: dict[str, Any], reason: str) -> None:
    with pytest.raises(ValidationError, match=reason):
        c.Notification.model_validate(payload)


@pytest.mark.parametrize(
    "payload",
    [
        PROGRESS | {"step_code": "unknown_step"},
        SYSTEM | {"message_code": "Serwis nie działa."},
    ],
)
def test_free_text_is_rejected(payload: dict[str, Any]) -> None:
    with pytest.raises(ValidationError):
        c.Notification.model_validate(payload)


def test_schema_describes_the_codes() -> None:
    props = c.Notification.model_json_schema()["properties"]
    assert "check_progress only" in props["step_code"]["description"]
    assert "system only" in props["message_code"]["description"]
