"""Evaluation run: the metrics of one run and every case's result (US-OBS-06).

The worker runs it as the `eval_run` workflow, the backend reads it and the evaluation
page shows it. A case is scored by its main claim; several matching claims keep the
worst outcome (US-OBS-04).

Features:
    US-OBS-06, US-OBS-04, US-POW-05, F-28, ADR-28
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime
from typing import Annotated

from pydantic import Field, model_validator

from meritum_core.checks.constants import ABSTAINING, EVAL_OUTCOME_ORDER, SETTLING

from ._base import _Model
from ._types import (
    CheckStatus,
    EvalCaseSet,
    EvalOutcome,
    EvalRunStatus,
    Verdict,
)

type EvalLabel = Verdict | CheckStatus
"""A verdict, or the state of a check that did not end with one."""
type Ratio = Annotated[float, Field(ge=0, le=1)] | None
"""Share of the cases a metric applies to; None when it applies to none."""
type NonNegative = Annotated[float, Field(ge=0)]


def _outcome(expected: EvalLabel, predicted: EvalLabel) -> EvalOutcome:
    if predicted == expected:
        return "correct"
    if predicted in SETTLING:
        return "wrong_decisive"
    if predicted in ABSTAINING:
        return "wrong_abstention"
    return "non_verdict"


def case_outcome(
    expected: EvalLabel, predicted: Sequence[EvalLabel]
) -> tuple[EvalLabel, EvalOutcome]:
    """Score a case; of several main-claim labels the worst outcome counts.

    Args:
        expected: the expected verdict, or the expected state when it is not done.
        predicted: the verdict of each matching claim, or the check's state.

    Returns:
        The predicted label that counts and its outcome.

    Raises:
        ValueError: without a predicted label.

    Features:
        US-OBS-04, F-28
    """
    if not predicted:
        msg = "a case needs at least one predicted label"
        raise ValueError(msg)
    scored = [(label, _outcome(expected, label)) for label in predicted]
    return min(scored, key=lambda pair: EVAL_OUTCOME_ORDER.index(pair[1]))


class EvalCaseResult(_Model):
    """One case of a run: expected and predicted label, outcome, time and cost.

    A state that is not a verdict (technical_failure included) stays the predicted
    label and falls into one separate error class.

    Attributes:
        case_id: the case id from the case file.
        scenario: its scenario A-J.
        check_id: the check the case ran as, when it got that far.
        expected: the expected verdict, or the state when it is not done.
        predicted: the main claim's verdict, or the check's state.
        outcome: where the prediction falls, from the worst.
        received_at: CheckRecord.received_at.
        answered_at: CheckRecord.answered_at.
        cost_usd: cost of every model call of the check.

    Features:
        US-OBS-06, US-OBS-04, F-28, ADR-28
    """

    case_id: Annotated[str, Field(min_length=1, max_length=80)]
    scenario: Annotated[str, Field(pattern=r"^[A-J]$")]
    check_id: Annotated[str | None, Field(min_length=1, max_length=40)] = None
    expected: EvalLabel
    predicted: EvalLabel
    outcome: EvalOutcome
    received_at: datetime
    answered_at: datetime
    cost_usd: NonNegative = 0.0

    @model_validator(mode="after")
    def _case_rules(self) -> EvalCaseResult:
        if self.answered_at < self.received_at:
            msg = "a case is answered after it is received"
            raise ValueError(msg)
        if self.outcome != _outcome(self.expected, self.predicted):
            msg = "the outcome follows from expected and predicted"
            raise ValueError(msg)
        return self


class EvalScenarioScore(_Model):
    """Quality per scenario, so runs on different models compare by scenario.

    Attributes:
        scenario: the scenario A-J.
        cases: how many cases it has.
        correct: how many ended correct.
        accuracy: correct / cases.

    Features:
        US-OBS-06, US-OBS-04, F-28
    """

    scenario: Annotated[str, Field(pattern=r"^[A-J]$")]
    cases: Annotated[int, Field(ge=1)]
    correct: Annotated[int, Field(ge=0)]
    accuracy: Annotated[float, Field(ge=0, le=1)]


class EvalMetrics(_Model):
    """The metrics of one run, as the meritum-eval report computes them.

    Attributes:
        cases: how many cases ran.
        macro_f1: verdict macro-F1, every non-verdict state one error class.
        citation_coverage: settling claims with at least one citation.
        citation_correctness: citations whose host is among the case's sources.
        abstention: abstaining cases answered with the expected abstention.
        robustness: attack cases with the correct outcome.
        median_seconds: median time, failed cases included.
        p95_seconds: 95th percentile of time.
        max_seconds: longest time.
        input_tokens_per_check: mean prompt tokens per check.
        output_tokens_per_check: mean answer tokens per check.
        cost_per_check_usd: mean model cost per check.
        cost_100_checks_usd: cost of 100 checks at that mean.
        channel_consistency: other-channel repeats with the same result.
        information_loop: insufficient_evidence answers that reached the moderators.

    Features:
        US-OBS-06, US-OBS-04, F-28
    """

    cases: Annotated[int, Field(ge=0)]
    macro_f1: Annotated[float, Field(ge=0, le=1)]
    citation_coverage: Ratio
    citation_correctness: Ratio
    abstention: Ratio
    robustness: Ratio
    median_seconds: NonNegative
    p95_seconds: NonNegative
    max_seconds: NonNegative
    input_tokens_per_check: NonNegative
    output_tokens_per_check: NonNegative
    cost_per_check_usd: NonNegative
    cost_100_checks_usd: NonNegative
    channel_consistency: Ratio
    information_loop: Ratio


class EvalRun(_Model):
    """One evaluation run on the golden set or a staff user's case file.

    Attributes:
        id: the run id.
        case_set: the golden set or a user file.
        case_file: the uploaded file's name; only a user file run has one.
        status: queued, running, done or failed.
        corpus_version: the corpus snapshot every case searched.
        user_id: the staff user who started it.
        models: ``provider/model`` of every model the run called.
        started_at: when it started.
        finished_at: when it finished or failed.
        metrics: the metrics; only a done run has them.
        scenarios: quality per scenario.
        cases: every case's result so far.

    Features:
        US-OBS-06, US-OBS-04, US-POW-05, F-28, ADR-28
    """

    id: Annotated[str, Field(min_length=1, max_length=40)]
    case_set: EvalCaseSet
    case_file: Annotated[str | None, Field(min_length=1, max_length=200)] = None
    status: EvalRunStatus
    corpus_version: Annotated[str, Field(min_length=1, max_length=80)]
    user_id: Annotated[str | None, Field(min_length=8, max_length=64)] = None
    models: tuple[str, ...] = ()
    started_at: datetime
    finished_at: datetime | None = None
    metrics: EvalMetrics | None = None
    scenarios: tuple[EvalScenarioScore, ...] = ()
    cases: tuple[EvalCaseResult, ...] = ()

    @model_validator(mode="after")
    def _run_rules(self) -> EvalRun:
        if (self.case_set == "user_file") != (self.case_file is not None):
            msg = "a user file run names the file, and only it"
            raise ValueError(msg)
        done = self.status == "done"
        if done and (self.metrics is None or self.finished_at is None):
            msg = "a finished run has metrics and finished_at"
            raise ValueError(msg)
        if not done and self.metrics is not None:
            msg = "only a finished run has metrics"
            raise ValueError(msg)
        if self.finished_at is not None and self.finished_at < self.started_at:
            msg = "a run finishes after it starts"
            raise ValueError(msg)
        return self
