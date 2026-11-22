"""Models of the `eval_run` workflow: one evaluation run a staff user started.

Features:
    US-OBS-06, US-POW-05, F-28, ADR-28, ADR-03
"""

from typing import Annotated

from pydantic import Field

from meritum_core.checks.contracts import EvalCaseSet, EvalRun
from meritum_core.jobs.contracts._base import Identifier, JobModel


class EvalRunInput(JobModel):
    """Input of the `eval_run` workflow.

    Attributes:
        run_id: the EvalRun id the worker writes.
        case_set: the golden set or an uploaded file.
        case_file: the uploaded file's name; only a user file run has one.
        corpus_version: the corpus snapshot every case searches.
        user_id: the staff user who started it; gets the eval_run_done notification.

    Features:
        US-OBS-06, US-POW-05, F-28, ADR-28
    """

    run_id: Annotated[str, Field(min_length=1, max_length=40)]
    case_set: EvalCaseSet
    case_file: Annotated[str | None, Field(min_length=1, max_length=200)] = None
    corpus_version: Annotated[str, Field(min_length=1, max_length=80)]
    user_id: Identifier


class EvalRunOutput(JobModel):
    """Output of the `eval_run` workflow: the finished or failed run.

    Attributes:
        run: the run as stored.

    Features:
        US-OBS-06, F-28, ADR-28
    """

    run: EvalRun
