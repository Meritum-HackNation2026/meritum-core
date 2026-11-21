"""Ports of the notifications slice: the inbox store.

Features:
    US-POW-01, US-BEZ-05, F-22, ADR-13
"""

from collections.abc import Sequence
from datetime import datetime
from typing import Literal, Protocol

from meritum_core.checks.contracts import Notification

type RecipientKind = Literal["session_id", "user_id"]
"""The Notification field that names its recipient.

Discord, SMS and MCP users are named by ``session_id``, which equals their
channel user hash there.
"""


class NotificationRepository(Protocol):
    """Stores inbox notifications (port).

    The worker saves them, the backend lists them and marks them read. Every
    adapter passes the contract test in ``tests/notifications/``.

    Features:
        US-POW-01, US-BEZ-05, F-22, ADR-13
    """

    async def save(self, notification: Notification) -> None:
        """Store ``notification``, replacing a stored one with the same id.

        Args:
            notification: the notification to store.
        """
        ...

    async def list_for(self, kind: RecipientKind, value: str) -> list[Notification]:
        """List one recipient's notifications, newest ``created_at`` first.

        Args:
            kind: whether the recipient is a session or an account.
            value: the session id or user id.

        Returns:
            The recipient's notifications.
        """
        ...

    async def mark_read(self, notification_id: str) -> None:
        """Mark one notification as read; an unknown id does nothing.

        Args:
            notification_id: the notification's id.
        """
        ...

    async def delete_for(self, kind: RecipientKind, value: str) -> int:
        """Delete every notification of one recipient (US-BEZ-05).

        Args:
            kind: whether the recipient is a session or an account.
            value: the session id or user id.

        Returns:
            How many notifications were deleted.
        """
        ...

    async def delete_for_checks(self, check_ids: Sequence[str]) -> int:
        """Delete every notification about one of the given checks (US-BEZ-05).

        A deleted check takes its notifications along, whoever they went to.

        Args:
            check_ids: the deleted checks.

        Returns:
            How many notifications were deleted.
        """
        ...

    async def delete_expired(self, now: datetime) -> int:
        """Delete notifications whose ``retention_until`` has passed (ADR-13).

        Args:
            now: the retention run's time.

        Returns:
            How many notifications were deleted.
        """
        ...
