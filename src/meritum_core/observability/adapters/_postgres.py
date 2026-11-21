"""PostgreSQL SubjectEraser: one transaction over every app table.

Features:
    US-BEZ-05, F-24, ADR-13
"""

from psycopg import AsyncConnection

from meritum_core.checks import SubjectKind
from meritum_core.checks.adapters import delete_subject_records
from meritum_core.moderation.adapters import remove_case_checks
from meritum_core.notifications.adapters import (
    delete_check_notifications,
    delete_recipient_notifications,
)
from meritum_core.observability.constants import SUBJECT_RECIPIENT


class PostgresSubjectEraser:
    """SubjectEraser that deletes from all app tables in one transaction.

    Args:
        conninfo: libpq connection string; its ``search_path`` names the app schema.

    Features:
        US-BEZ-05, F-24, ADR-13
    """

    def __init__(self, conninfo: str) -> None:
        self._conninfo = conninfo

    async def erase(self, kind: SubjectKind, value: str) -> int:
        """Erase one person's records, notifications and case checks, all or nothing.

        Args:
            kind: which identifier names the person.
            value: its value.

        Returns:
            How many records and notifications were deleted.
        """
        recipient = SUBJECT_RECIPIENT[kind]
        async with (
            await AsyncConnection.connect(self._conninfo) as conn,
            conn.transaction(),
        ):
            check_ids = await delete_subject_records(conn, kind, value)
            await remove_case_checks(conn, check_ids)
            notes = await delete_recipient_notifications(conn, recipient, value)
            notes += await delete_check_notifications(conn, check_ids)
        return len(check_ids) + notes
