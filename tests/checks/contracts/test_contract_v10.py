"""Contract v10: an evaluation run with case results and its end notification.

Features:
    US-OBS-06, US-OBS-04, US-POW-05, F-28, ADR-28
"""

from typing import Any

import pytest
from pydantic import ValidationError
from tests.checks.contracts.samples import EXAMPLES

from meritum_core.checks import contracts as c
from meritum_core.jobs.contracts import EVAL_RUN, WORKFLOWS, EvalRunInput

RUN: dict[str, Any] = EXAMPLES["EvalRun"]
CASE: dict[str, Any] = RUN["cases"][0]
NOTE: dict[str, Any] = EXAMPLES["Notification.eval_run_done"]


def test_example_run_is_valid() -> None:
    run = c.EvalRun.model_validate(RUN)
    assert run.metrics is not None
    assert run.cases[0].outcome == "correct"


@pytest.mark.parametrize(
    ("payload", "reason"),
    [
        ({k: v for k, v in RUN.items() if k != "corpus_version"}, "corpus_version"),
        (RUN | {"corpus_version": ""}, "corpus_version"),
        (RUN | {"metrics": None}, "a finished run has metrics"),
        (RUN | {"finished_at": None}, "a finished run has metrics"),
        (RUN | {"status": "running"}, "only a finished run has metrics"),
        (RUN | {"finished_at": "2026-11-22T09:00:00+01:00"}, "finishes after"),
        (RUN | {"case_set": "user_file"}, "a user file run names the file"),
        (RUN | {"case_file": "jury.csv"}, "a user file run names the file"),
    ],
)
def test_bad_runs_are_rejected(payload: dict[str, Any], reason: str) -> None:
    with pytest.raises(ValidationError, match=reason):
        c.EvalRun.model_validate(payload)


def test_running_run_has_no_metrics_yet() -> None:
    run = c.EvalRun.model_validate(
        RUN | {"status": "running", "metrics": None, "finished_at": None}
    )
    assert run.metrics is None


@pytest.mark.parametrize(
    ("payload", "reason"),
    [
        ({k: v for k, v in CASE.items() if k != "answered_at"}, "answered_at"),
        ({k: v for k, v in CASE.items() if k != "received_at"}, "received_at"),
        (CASE | {"answered_at": "2026-11-22T09:59:00+01:00"}, "answered after"),
        (CASE | {"predicted": "technical_failure"}, "outcome follows"),
        (CASE | {"cost_usd": -1}, "cost_usd"),
    ],
)
def test_bad_case_results_are_rejected(payload: dict[str, Any], reason: str) -> None:
    with pytest.raises(ValidationError, match=reason):
        c.EvalCaseResult.model_validate(payload)


def test_failure_is_its_own_error_class() -> None:
    case = c.EvalCaseResult.model_validate(
        CASE | {"predicted": "technical_failure", "outcome": "non_verdict"}
    )
    assert case.outcome == "non_verdict"


@pytest.mark.parametrize(
    ("expected", "predicted", "worst"),
    [
        ("false", ["false"], ("false", "correct")),
        ("false", ["false", "confirmed"], ("confirmed", "wrong_decisive")),
        (
            "false",
            ["insufficient_evidence", "false"],
            ("insufficient_evidence", "wrong_abstention"),
        ),
        ("false", ["technical_failure"], ("technical_failure", "non_verdict")),
        ("out_of_scope", ["out_of_scope"], ("out_of_scope", "correct")),
        ("insufficient_evidence", ["false"], ("false", "wrong_decisive")),
    ],
)
def test_worst_outcome_keeps_the_worst(
    expected: c.Verdict | c.CheckStatus,
    predicted: list[c.Verdict | c.CheckStatus],
    worst: tuple[str, str],
) -> None:
    assert c.case_outcome(expected, predicted) == worst


def test_case_outcome_needs_a_prediction() -> None:
    with pytest.raises(ValueError, match="at least one"):
        c.case_outcome("false", [])


def test_run_done_note_goes_to_a_signed_in_user() -> None:
    assert c.Notification.model_validate(NOTE).user_id == "u_9f2a7c31"
    session = {k: v for k, v in NOTE.items() if k != "user_id"}
    with pytest.raises(ValidationError, match="'eval_run_done' goes to a staff user"):
        c.Notification.model_validate(session | {"session_id": "s_7f3a9c21"})


def test_eval_run_workflow_is_registered() -> None:
    assert EVAL_RUN in WORKFLOWS
    payload = EvalRunInput(
        run_id="ev_0001",
        case_set="golden",
        corpus_version="2026-11-22",
        user_id="u_9f2a7c31",
    )
    assert EVAL_RUN.input.model_validate(payload.model_dump(mode="json")) == payload


def test_contract_version_is_10() -> None:
    assert c.CONTRACT_VERSION == 10
