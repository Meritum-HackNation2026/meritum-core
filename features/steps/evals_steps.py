"""Steps for contract v10: an evaluation run, its case results and its notification.

Features:
    US-OBS-06, US-OBS-04, US-POW-05, F-28, ADR-28
"""

import json
from pathlib import Path
from typing import Any

from behave import given, then, when
from behave.runner import Context

from meritum_core.checks.contracts import EvalCaseResult, EvalRun, Notification

EXAMPLES: dict[str, Any] = json.loads(
    (Path(__file__).resolve().parents[2] / "contracts" / "examples.json").read_text(
        "utf-8"
    )
)
METRICS = (
    "macro_f1",
    "citation_coverage",
    "citation_correctness",
    "abstention",
    "robustness",
    "median_seconds",
    "max_seconds",
    "cost_100_checks_usd",
    "channel_consistency",
    "information_loop",
)


@given("przebieg na golden secie z przypiętym corpus_version")
def given_golden_run(context: Context) -> None:
    """A finished run on the golden set."""
    context.payload = EXAMPLES["EvalRun"]


@when("worker zapisuje EvalRun")
def when_run_is_saved(context: Context) -> None:
    """Validate the run."""
    context.run = EvalRun.model_validate(context.payload)


@then(
    "EvalRun ma zestaw, datę, corpus_version, stan, mierniki i wynik każdego przypadku"
)
def then_run_is_complete(context: Context) -> None:
    """The run carries its set, dates, corpus, state, metrics and cases."""
    run = context.run
    assert run.case_set == "golden"
    assert run.corpus_version
    assert run.status == "done"
    assert run.finished_at is not None
    assert run.metrics is not None
    assert run.cases


@then(
    "mierniki obejmują macro-F1, pokrycie i poprawność cytowań, wstrzymanie, "
    "odporność, medianę i maksimum czasu, koszt 100 testów, spójność kanałów "
    "i pętlę informacji"
)
def then_metrics_are_named(context: Context) -> None:
    """Every metric of the brief is a field of EvalMetrics."""
    assert set(METRICS) <= set(type(context.run.metrics).model_fields)


@given('przypadek, którego sprawdzenie skończyło się stanem "{status}"')
def given_case_with_status(context: Context, status: str) -> None:
    """A case result whose check ended in a state that is not a verdict."""
    context.payload = EXAMPLES["EvalRun"]["cases"][0] | {
        "predicted": status,
        "outcome": "non_verdict",
    }
    context.status = status


@when("worker zapisuje wynik przypadku")
def when_case_is_saved(context: Context) -> None:
    """Validate the case result."""
    context.case = EvalCaseResult.model_validate(context.payload)


@then(
    "wynik ma ten stan jako osobną klasę błędu i czas z CheckRecord, "
    "a walidacja go przyjmuje"
)
def then_case_is_non_verdict(context: Context) -> None:
    """The state stays the prediction and falls into the non-verdict class."""
    case = context.case
    assert case.predicted == context.status
    assert case.outcome == "non_verdict"
    assert case.answered_at >= case.received_at


@given("analityk uruchomił przebieg")
def given_analyst_started_run(context: Context) -> None:
    """The analyst who started the run."""
    context.payload = EXAMPLES["Notification.eval_run_done"]


@when("przebieg się kończy")
def when_run_finishes(context: Context) -> None:
    """Build the end-of-run notification."""
    context.note = Notification.model_validate(context.payload)


@then('Notification ma rodzaj "{kind}", user_id analityka i link do przebiegu')
def then_note_names_run(context: Context, kind: str) -> None:
    """The notification goes to the analyst and links the run."""
    note = context.note
    assert note.kind == kind
    assert note.user_id is not None
    assert note.link.startswith("/eval/")
