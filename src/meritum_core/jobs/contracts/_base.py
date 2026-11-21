"""Base model of every job payload: versioned, frozen, no unknown fields.

Features:
    ADR-03
"""

from pydantic import BaseModel, ConfigDict

from meritum_core.jobs.constants import CONTRACT_VERSION


class JobModel(BaseModel):
    """A workflow input or output sent as one portable JSON object.

    Unknown fields are rejected, so nothing (a raw channel user id included)
    rides along unnoticed.

    Attributes:
        contract_version: the job contract version the sender speaks.

    Features:
        ADR-03
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    contract_version: int = CONTRACT_VERSION
