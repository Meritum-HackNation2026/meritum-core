"""Models of the `check` workflow: one masked request in, one result out.

Features:
    US-SPR-01, US-SPR-02, F-09, ADR-03
"""

from datetime import datetime
from typing import Annotated, Self

from pydantic import Field, model_validator

from meritum_core.checks import SESSIONLESS_CHANNELS, CheckRequest, CheckResult
from meritum_core.jobs.constants import HASH_PATTERN
from meritum_core.jobs.contracts._base import Identifier, JobModel


class CheckInput(JobModel):
    """Input of the `check` workflow, built by the backend from a channel request.

    The backend masks personal data in `request` before enqueueing, hashes
    `request.channel_user_id` into `channel_user_hash` and clears it from `request`.
    The channel user id reaches the workflow only in that hashed form: DBOS stores the
    input, so a request still carrying the raw id is rejected.

    Attributes:
        request: the channel's request with personal data already masked.
        session_id: browser session id; on Discord, SMS and MCP the user hash.
        user_id: the signed-in user's id, if any; web and extension only, since
            Discord, SMS and MCP have no sign-in.
        channel_user_hash: Discord, SMS and MCP only: salted SHA-256 of the
            channel user id.
        received_at: when the backend received the request.

    Features:
        US-SPR-01, US-SPR-02, US-BEZ-05, US-BEZ-06, F-09, ADR-03
    """

    request: CheckRequest
    session_id: Identifier | None = None
    user_id: Identifier | None = None
    channel_user_hash: Annotated[str | None, Field(pattern=HASH_PATTERN)] = None
    received_at: datetime

    @model_validator(mode="after")
    def _identity(self) -> Self:
        if self.session_id is None and self.user_id is None:
            msg = "a check comes from a session or a signed-in user"
            raise ValueError(msg)
        is_sessionless = self.request.channel in SESSIONLESS_CHANNELS
        if is_sessionless and self.user_id is not None:
            msg = "Discord, SMS and MCP have no signed-in user"
            raise ValueError(msg)
        if is_sessionless != (self.channel_user_hash is not None):
            msg = "only Discord, SMS and MCP carry a hashed channel user id, always"
            raise ValueError(msg)
        if is_sessionless and self.session_id != self.channel_user_hash:
            msg = "on Discord, SMS and MCP the session id is the hashed user id"
            raise ValueError(msg)
        return self

    @model_validator(mode="after")
    def _no_raw_channel_user_id(self) -> Self:
        if self.request.channel_user_id is not None:
            msg = "the raw channel user id never enters a job; send channel_user_hash"
            raise ValueError(msg)
        return self


class CheckOutput(JobModel):
    """Output of the `check` workflow.

    Attributes:
        result: the answer every channel renders.

    Features:
        US-SPR-01, F-09, ADR-03
    """

    result: CheckResult
