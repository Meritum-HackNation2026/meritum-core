"""Inbox notifications pushed live and kept as unread until acted on.

Features:
    US-POW-01, US-POW-04, F-26, ADR-02, ADR-29
"""

from __future__ import annotations

from datetime import datetime
from typing import Annotated, Literal

from pydantic import Field, model_validator

from meritum_core.checks.constants import CASE_KINDS, CHECK_KINDS

from ._base import _Model
from ._types import AnalysisStepCode, NotificationKind, SystemMessageCode


def _code_for_kind(
    kind: NotificationKind, owner: NotificationKind, code: str | None, what: str
) -> None:
    if (kind == owner) != (code is not None):
        raise ValueError(
            f"{owner!r} names {what}"
            if code is None
            else f"only {owner!r} names {what}"
        )


class Notification(_Model):
    """An inbox entry, pushed live over SSE or WebSocket from DBOS events and shown as a toast.

    A toast the recipient did not act on stays in the inbox as unread. Addressed to one browser session or one
    signed-in user (staff included). Text comes from copy/pl.json by `kind`.

    Attributes:
        id: the notification id.
        kind: what the notification is about.
        status: unread or read.
        session_id: the recipient browser session.
        user_id: the recipient signed-in user.
        check_id: the check it is about.
        case_id: the moderator case it is about.
        step_code: the pipeline step a check_progress notification reports.
        message_code: what a system notification says.
        link: the in-app path to open.
        created_at: when it was created.
        retention_until: when it is deleted.

    Features:
        US-POW-01, US-POW-02, US-POW-03, US-POW-04, US-POW-05, US-MOD-07, F-26, ADR-02,
        ADR-29
    """

    id: Annotated[str, Field(min_length=1, max_length=40)]
    kind: NotificationKind
    status: Literal["unread", "read"] = "unread"
    session_id: Annotated[str | None, Field(min_length=8, max_length=64)] = None
    user_id: Annotated[str | None, Field(min_length=8, max_length=64)] = None
    check_id: Annotated[str | None, Field(min_length=1, max_length=40)] = None
    case_id: Annotated[str | None, Field(pattern=r"^#S-\d+$")] = None
    step_code: Annotated[
        AnalysisStepCode | None,
        Field(
            description="check_progress only: the finished pipeline step; the text "
            "is analysis.steps.<code> in copy/pl.json."
        ),
    ] = None
    message_code: Annotated[
        SystemMessageCode | None,
        Field(
            description="system only: what the message says; the text is "
            "notifications.system_message.<code> in copy/pl.json, never free text."
        ),
    ] = None
    link: Annotated[
        str,
        Field(pattern=r"^/\S*$", max_length=200, description="In-app path to open."),
    ]
    created_at: datetime
    retention_until: datetime

    @model_validator(mode="after")
    def _notification_rules(self) -> Notification:
        if (self.session_id is None) == (self.user_id is None):
            raise ValueError("a notification goes to one session or one signed-in user")
        if self.kind in CHECK_KINDS and self.check_id is None:
            raise ValueError(f"{self.kind!r} names the check")
        if self.kind in CASE_KINDS and self.case_id is None:
            raise ValueError(f"{self.kind!r} names the case")
        _code_for_kind(self.kind, "check_progress", self.step_code, "a step")
        _code_for_kind(self.kind, "system", self.message_code, "a message code")
        if self.retention_until <= self.created_at:
            raise ValueError("retention ends after the notification was created")
        return self
