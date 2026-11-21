"""In-memory NotificationRepository for the tests of meritum-backend and meritum-worker.

Features:
    US-POW-01, US-BEZ-05, F-22
"""

from collections.abc import Callable
from datetime import datetime

from meritum_core.checks.contracts import Notification
from meritum_core.notifications.ports import RecipientKind


class InMemoryNotificationRepository:
    """NotificationRepository fake that keeps the notifications in a dict.

    Features:
        US-POW-01, US-BEZ-05, F-22
    """

    def __init__(self) -> None:
        self._notes: dict[str, Notification] = {}

    async def save(self, notification: Notification) -> None:
        """Store ``notification`` under its id.

        Args:
            notification: the notification to store.
        """
        self._notes[notification.id] = notification

    async def list_for(self, kind: RecipientKind, value: str) -> list[Notification]:
        """List one recipient's notifications, newest first.

        Args:
            kind: whether the recipient is a session or an account.
            value: its id.

        Returns:
            The notifications.
        """
        found = [n for n in self._notes.values() if getattr(n, kind) == value]
        return sorted(found, key=lambda n: n.created_at, reverse=True)

    async def mark_read(self, notification_id: str) -> None:
        """Mark one notification as read, if present.

        Args:
            notification_id: the notification's id.
        """
        note = self._notes.get(notification_id)
        if note is not None:
            self._notes[note.id] = note.model_copy(update={"status": "read"})

    async def delete_for(self, kind: RecipientKind, value: str) -> int:
        """Delete one recipient's notifications.

        Args:
            kind: whether the recipient is a session or an account.
            value: its id.

        Returns:
            How many were deleted.
        """
        return self._delete_where(lambda n: getattr(n, kind) == value)

    async def delete_expired(self, now: datetime) -> int:
        """Delete notifications past retention.

        Args:
            now: the retention run's time.

        Returns:
            How many were deleted.
        """
        return self._delete_where(lambda n: n.retention_until <= now)

    def _delete_where(self, matches: Callable[[Notification], bool]) -> int:
        gone = [i for i, n in self._notes.items() if matches(n)]
        for note_id in gone:
            del self._notes[note_id]
        return len(gone)
