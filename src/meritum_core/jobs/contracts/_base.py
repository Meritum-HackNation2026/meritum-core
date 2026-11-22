"""Base model of every job payload: versioned, frozen, no unknown fields.

Features:
    ADR-03
"""

from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field

from meritum_core.jobs.constants import CONTRACT_VERSION, ID_MAX_CHARS, ID_MIN_CHARS

Identifier = Annotated[str, Field(min_length=ID_MIN_CHARS, max_length=ID_MAX_CHARS)]
"""A session id, a user id or a channel user hash."""


class JobModel(BaseModel):
    """A workflow input or output sent as one portable JSON object.

    Unknown fields are rejected when a payload is built, so nothing (a raw channel
    user id included) rides along unnoticed. A reader of the queue validates with
    `extra="ignore"` and the sender drops None fields, so a backend and a worker on
    different contract versions still understand each other (core#140).

    Attributes:
        contract_version: the job contract version the sender speaks.

    Features:
        ADR-03
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    contract_version: int = CONTRACT_VERSION
