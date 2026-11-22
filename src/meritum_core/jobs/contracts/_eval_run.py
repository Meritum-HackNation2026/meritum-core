"""Models of the `eval_run` workflow: one evaluation run a staff user started.

Features:
    US-OBS-06, US-POW-05, F-28, ADR-28, ADR-03
"""

from typing import Annotated

from pydantic import Field, model_validator

from meritum_core.checks.contracts import EvalCaseSet, EvalRun
from meritum_core.jobs.contracts._base import Identifier, JobModel
from meritum_core.shared.blobs import BLOB_ID_PATTERN, BlobKind


class EvalRunInput(JobModel):
    """Input of the `eval_run` workflow.

    Attributes:
        run_id: the EvalRun id the worker writes.
        case_set: the golden set or an uploaded file.
        case_file: the uploaded file's name; only a user file run has one.
        dataset_blob_id: the blob store id of the uploaded case file (from v5);
            only a user file run has one, and an older sender may leave it out.
        corpus_version: the corpus snapshot every case searches.
        user_id: the staff user who started it; gets the eval_run_done notification.

    Features:
        US-OBS-06, US-POW-05, F-28, ADR-28
    """

    run_id: Annotated[str, Field(min_length=1, max_length=40)]
    case_set: EvalCaseSet
    case_file: Annotated[str | None, Field(min_length=1, max_length=200)] = None
    dataset_blob_id: Annotated[str | None, Field(pattern=BLOB_ID_PATTERN)] = None
    corpus_version: Annotated[str, Field(min_length=1, max_length=80)]
    user_id: Identifier

    @model_validator(mode="after")
    def _blob_belongs_to_a_user_file(self) -> EvalRunInput:
        if self.dataset_blob_id is not None and self.case_set != "user_file":
            msg = "only a user file run names a dataset blob"
            raise ValueError(msg)
        if self.dataset_blob_id is not None and not self.dataset_blob_id.startswith(
            f"{BlobKind.DATASET}_"
        ):
            msg = "the dataset blob is a dataset kind blob"
            raise ValueError(msg)
        return self


class EvalRunOutput(JobModel):
    """Output of the `eval_run` workflow: the finished or failed run.

    Attributes:
        run: the run as stored.

    Features:
        US-OBS-06, F-28, ADR-28
    """

    run: EvalRun
