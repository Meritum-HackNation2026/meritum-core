"""Constants of the observability slice.

Features:
    US-BEZ-05, F-24
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Final

if TYPE_CHECKING:
    from meritum_core.checks import SubjectKind
    from meritum_core.notifications import RecipientKind

SUBJECT_RECIPIENT: Final[dict[SubjectKind, RecipientKind]] = {
    "session_id": "session_id",
    "user_id": "user_id",
    "channel_user_hash": "session_id",
}
"""The Notification field that names each subject; Discord, SMS and MCP users get
notifications under ``session_id``, which equals their channel user hash."""
