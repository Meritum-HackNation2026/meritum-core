"""PostgreSQL CheckRecordRepository over the ``check_records`` table of the app schema.

Features:
    US-OBS-01, US-BEZ-05, F-22, F-24, ADR-13
"""

import operator
from collections.abc import Sequence
from datetime import datetime
from itertools import starmap
from typing import Final

from psycopg import AsyncConnection, sql
from psycopg.types.json import Jsonb

from meritum_core.checks.contracts import CheckRecord
from meritum_core.checks.ports import SubjectKind

_COLUMN: Final[dict[SubjectKind, sql.Identifier]] = {
    "session_id": sql.Identifier("session_id"),
    "user_id": sql.Identifier("user_id"),
    "channel_user_hash": sql.Identifier("channel_user_hash"),
}
"""The column of each subject kind; a fixed map, so no caller text reaches the SQL."""


async def delete_subject_records(
    conn: AsyncConnection, kind: SubjectKind, value: str
) -> list[str]:
    """Delete one person's records on an open connection, inside its transaction.

    Args:
        conn: the connection; the caller owns the transaction.
        kind: which field names the person.
        value: the session id, user id or channel user hash.

    Returns:
        The deleted ``check_id`` values, newest ``received_at`` first.

    Features:
        US-BEZ-05, F-24
    """
    query = sql.SQL(
        "DELETE FROM check_records WHERE {} = %s RETURNING check_id, received_at"
    ).format(_COLUMN[kind])
    cursor = await conn.execute(query, (value,))
    rows = sorted(await cursor.fetchall(), key=operator.itemgetter(1), reverse=True)
    return [check_id for check_id, _ in rows]


class PostgresCheckRecordRepository:
    """CheckRecordRepository that keeps each record as jsonb (see the port).

    Args:
        conninfo: libpq connection string; its ``search_path`` names the app schema.

    Features:
        US-OBS-01, US-BEZ-05, F-22, F-24, ADR-13
    """

    def __init__(self, conninfo: str) -> None:
        self._conninfo = conninfo

    async def _connect(self) -> AsyncConnection:
        # shortcut: one connection per call; take a pool from the caller when
        # the API's request rate makes connecting a cost.
        return await AsyncConnection.connect(self._conninfo)

    async def save(self, record: CheckRecord) -> None:
        """Store or replace ``record``.

        Args:
            record: the record to store.
        """
        row = (
            record.check_id,
            record.session_id,
            record.user_id,
            record.channel_user_hash,
            record.received_at,
            record.retention_until,
            Jsonb(record.model_dump(mode="json")),
        )
        async with await self._connect() as conn:
            await conn.execute(
                "INSERT INTO check_records (check_id, session_id, user_id,"
                " channel_user_hash, received_at, retention_until, record)"
                " VALUES (%s, %s, %s, %s, %s, %s, %s)"
                " ON CONFLICT (check_id) DO UPDATE SET"
                " session_id = EXCLUDED.session_id,"
                " user_id = EXCLUDED.user_id,"
                " channel_user_hash = EXCLUDED.channel_user_hash,"
                " received_at = EXCLUDED.received_at,"
                " retention_until = EXCLUDED.retention_until, record = EXCLUDED.record",
                row,
            )

    async def get(self, check_id: str) -> CheckRecord | None:
        """Read one record.

        Args:
            check_id: the check's id.

        Returns:
            The record or None.
        """
        async with await self._connect() as conn:
            cursor = await conn.execute(
                "SELECT record FROM check_records WHERE check_id = %s", (check_id,)
            )
            row = await cursor.fetchone()
        return None if row is None else _record(row[0])

    async def list_for(self, kind: SubjectKind, value: str) -> list[CheckRecord]:
        """List one person's records, newest first.

        Args:
            kind: which field names the person.
            value: its value.

        Returns:
            The matching records.
        """
        query = sql.SQL(
            "SELECT record FROM check_records WHERE {} = %s"
            " ORDER BY received_at DESC, check_id"
        ).format(_COLUMN[kind])
        async with await self._connect() as conn:
            cursor = await conn.execute(query, (value,))
            rows = await cursor.fetchall()
        return list(starmap(_record, rows))

    async def list_between(
        self, start: datetime, end: datetime, limit: int
    ) -> list[CheckRecord]:
        """List records received in ``[start, end)``, newest first, then by check id.

        Args:
            start: inclusive, timezone-aware lower bound.
            end: exclusive, timezone-aware upper bound.
            limit: maximum records to return. Nonpositive limits return no records.

        Returns:
            Matching records across all subjects.
        """
        if limit <= 0:
            return []
        async with await self._connect() as conn:
            cursor = await conn.execute(
                "SELECT record FROM check_records"
                " WHERE received_at >= %s AND received_at < %s"
                " ORDER BY received_at DESC, check_id LIMIT %s",
                (start, end, limit),
            )
            rows = await cursor.fetchall()
        return list(starmap(_record, rows))

    async def delete_subject(self, kind: SubjectKind, value: str) -> list[str]:
        """Delete one person's records.

        Args:
            kind: which field names the person.
            value: its value.

        Returns:
            The deleted check ids.
        """
        async with await self._connect() as conn:
            return await delete_subject_records(conn, kind, value)

    async def expired(self, now: datetime, *, limit: int) -> list[str]:
        """Select records past retention, oldest first.

        Args:
            now: the retention run's time.
            limit: the most ids to return.

        Returns:
            The expired check ids.
        """
        async with await self._connect() as conn:
            cursor = await conn.execute(
                "SELECT check_id FROM check_records WHERE retention_until <= %s"
                " ORDER BY retention_until, check_id LIMIT %s",
                (now, limit),
            )
            rows = await cursor.fetchall()
        return [check_id for (check_id,) in rows]

    async def delete(self, check_ids: Sequence[str]) -> None:
        """Delete the given records, ignoring unknown ids.

        Args:
            check_ids: the records to delete.
        """
        async with await self._connect() as conn:
            await conn.execute(
                "DELETE FROM check_records WHERE check_id = ANY(%s)", (list(check_ids),)
            )


def _record(value: object) -> CheckRecord:
    # The worker may run a newer contract than this reader (core#140).
    return CheckRecord.model_validate(value, extra="ignore")
