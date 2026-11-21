"""PostgreSQL NotificationRepository over the ``notifications`` table of the app schema.

Features:
    US-POW-01, US-BEZ-05, F-22, ADR-13
"""

from datetime import datetime
from itertools import starmap
from typing import Final

from psycopg import AsyncConnection, sql
from psycopg.types.json import Jsonb

from meritum_core.checks.contracts import Notification
from meritum_core.notifications.ports import RecipientKind

_COLUMN: Final[dict[RecipientKind, sql.Identifier]] = {
    "session_id": sql.Identifier("session_id"),
    "user_id": sql.Identifier("user_id"),
}
"""The column of each recipient kind; a fixed map, so no caller text reaches the SQL."""


async def delete_recipient_notifications(
    conn: AsyncConnection, kind: RecipientKind, value: str
) -> int:
    """Delete one recipient's notifications inside the caller's transaction.

    Args:
        conn: the connection; the caller owns the transaction.
        kind: whether the recipient is a session or an account.
        value: the session id or user id.

    Returns:
        How many were deleted.

    Features:
        US-POW-01, US-BEZ-05, F-22
    """
    query = sql.SQL("DELETE FROM notifications WHERE {} = %s").format(_COLUMN[kind])
    cursor = await conn.execute(query, (value,))
    return cursor.rowcount


class PostgresNotificationRepository:
    """NotificationRepository that keeps each notification as jsonb (see the port).

    Args:
        conninfo: libpq connection string; its ``search_path`` names the app schema.

    Features:
        US-POW-01, US-BEZ-05, F-22, ADR-13
    """

    def __init__(self, conninfo: str) -> None:
        self._conninfo = conninfo

    async def _connect(self) -> AsyncConnection:
        # shortcut: one connection per call; take a pool from the caller when
        # the inbox's request rate makes connecting a cost.
        return await AsyncConnection.connect(self._conninfo)

    async def save(self, notification: Notification) -> None:
        """Store or replace ``notification``.

        Args:
            notification: the notification to store.
        """
        n = notification
        row = (n.id, n.session_id, n.user_id, n.created_at, n.retention_until)
        async with await self._connect() as conn:
            await conn.execute(
                "INSERT INTO notifications (id, session_id, user_id, created_at,"
                " retention_until, body) VALUES (%s, %s, %s, %s, %s, %s)"
                " ON CONFLICT (id) DO UPDATE SET session_id = EXCLUDED.session_id,"
                " user_id = EXCLUDED.user_id, created_at = EXCLUDED.created_at,"
                " retention_until = EXCLUDED.retention_until, body = EXCLUDED.body",
                (*row, Jsonb(n.model_dump(mode="json"))),
            )

    async def list_for(self, kind: RecipientKind, value: str) -> list[Notification]:
        """List one recipient's notifications, newest first.

        Args:
            kind: whether the recipient is a session or an account.
            value: its id.

        Returns:
            The notifications.
        """
        query = sql.SQL(
            "SELECT body FROM notifications WHERE {} = %s ORDER BY created_at DESC, id"
        ).format(_COLUMN[kind])
        async with await self._connect() as conn:
            cursor = await conn.execute(query, (value,))
            rows = await cursor.fetchall()
        return list(starmap(Notification.model_validate, rows))

    async def mark_read(self, notification_id: str) -> None:
        """Mark one notification as read, if present.

        Args:
            notification_id: the notification's id.
        """
        async with await self._connect() as conn:
            await conn.execute(
                "UPDATE notifications SET body = body || %s WHERE id = %s",
                (Jsonb({"status": "read"}), notification_id),
            )

    async def delete_for(self, kind: RecipientKind, value: str) -> int:
        """Delete one recipient's notifications.

        Args:
            kind: whether the recipient is a session or an account.
            value: its id.

        Returns:
            How many were deleted.
        """
        async with await self._connect() as conn:
            return await delete_recipient_notifications(conn, kind, value)

    async def delete_expired(self, now: datetime) -> int:
        """Delete notifications past retention.

        Args:
            now: the retention run's time.

        Returns:
            How many were deleted.
        """
        async with await self._connect() as conn:
            cursor = await conn.execute(
                "DELETE FROM notifications WHERE retention_until <= %s", (now,)
            )
            return cursor.rowcount
