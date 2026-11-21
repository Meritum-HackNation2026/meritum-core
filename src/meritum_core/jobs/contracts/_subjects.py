"""Models of the `delete_subject` workflow: erase one person's data.

Features:
    US-BEZ-05, ADR-03
"""

import re
from typing import Annotated, Self

from pydantic import Field, model_validator

from meritum_core.checks import SubjectKind
from meritum_core.jobs.constants import HASH_PATTERN
from meritum_core.jobs.contracts._base import Identifier, JobModel


class DeleteSubjectInput(JobModel):
    """Input of the `delete_subject` workflow.

    Attributes:
        kind: the kind of identifier.
        value: the session or user id, or the channel user hash (never the raw
            channel user id).

    Features:
        US-BEZ-05, ADR-03
    """

    kind: SubjectKind
    value: Identifier

    @model_validator(mode="after")
    def _hash_for_channel_users(self) -> Self:
        is_hash = re.fullmatch(HASH_PATTERN, self.value) is not None
        if self.kind == "channel_user_hash" and not is_hash:
            msg = "a channel user is named by the salted hash, never the raw id"
            raise ValueError(msg)
        return self


class DeleteSubjectOutput(JobModel):
    """Output of the `delete_subject` workflow.

    Attributes:
        deleted: how many stored items the workflow removed.

    Features:
        US-BEZ-05, ADR-03
    """

    deleted: Annotated[int, Field(ge=0)]
