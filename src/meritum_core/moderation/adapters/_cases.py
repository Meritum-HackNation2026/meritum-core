"""PostgreSQL ModeratorCaseRepository over the app schema's ``moderator_cases`` table.

Features:
    US-MOD-01, US-BEZ-05, F-25
"""

from collections.abc import Sequence
from itertools import starmap

from psycopg import AsyncConnection
from psycopg.types.json import Jsonb

from meritum_core.checks.contracts import CaseClaim, ModeratorCase
from meritum_core.moderation.ports import CaseState


async def remove_case_checks(conn: AsyncConnection, check_ids: Sequence[str]) -> None:
    """Drop checks from every case on an open connection, inside its transaction.

    A claim left without checks goes, and so does a case left without claims.

    Args:
        conn: the connection; the caller owns the transaction.
        check_ids: the deleted checks.

    Features:
        US-MOD-01, US-BEZ-05, F-25
    """
    gone = list(check_ids)
    if not gone:
        return
    cursor = await conn.execute(
        "SELECT body FROM moderator_cases WHERE EXISTS ("
        " SELECT 1 FROM jsonb_array_elements(body -> 'claims') AS c"
        " WHERE c -> 'check_ids' ?| %s) FOR UPDATE",
        (gone,),
    )
    for (body,) in await cursor.fetchall():
        case = ModeratorCase.model_validate(body)
        claims = _without(case.claims, set(gone))
        if claims:
            await _upsert(conn, case.model_copy(update={"claims": claims}))
        else:
            await conn.execute("DELETE FROM moderator_cases WHERE id = %s", (case.id,))


def _without(claims: list[CaseClaim], gone: set[str]) -> list[CaseClaim]:
    kept = [(c, [i for i in c.check_ids if i not in gone]) for c in claims]
    return [c.model_copy(update={"check_ids": ids}) for c, ids in kept if ids]


async def _upsert(conn: AsyncConnection, case: ModeratorCase) -> None:
    await conn.execute(
        "INSERT INTO moderator_cases (id, state, last_seen, body)"
        " VALUES (%s, %s, %s, %s)"
        " ON CONFLICT (id) DO UPDATE SET state = EXCLUDED.state,"
        " last_seen = EXCLUDED.last_seen, body = EXCLUDED.body",
        (case.id, case.state, case.last_seen, Jsonb(case.model_dump(mode="json"))),
    )


class PostgresModeratorCaseRepository:
    """ModeratorCaseRepository that keeps each case as jsonb (see the port).

    Args:
        conninfo: libpq connection string; its ``search_path`` names the app schema.

    Features:
        US-MOD-01, US-MOD-05, US-BEZ-05, F-25
    """

    def __init__(self, conninfo: str) -> None:
        self._conninfo = conninfo

    async def _connect(self) -> AsyncConnection:
        # shortcut: one connection per call; take a pool from the caller when
        # the panel's request rate makes connecting a cost.
        return await AsyncConnection.connect(self._conninfo)

    async def save(self, case: ModeratorCase) -> None:
        """Store or update ``case``.

        Args:
            case: the case to store.
        """
        async with await self._connect() as conn:
            await _upsert(conn, case)

    async def get(self, case_id: str) -> ModeratorCase | None:
        """Read one case.

        Args:
            case_id: the case's id.

        Returns:
            The case or None.
        """
        async with await self._connect() as conn:
            cursor = await conn.execute(
                "SELECT body FROM moderator_cases WHERE id = %s", (case_id,)
            )
            row = await cursor.fetchone()
        return None if row is None else ModeratorCase.model_validate(row[0])

    async def find_open(self, claim: str) -> ModeratorCase | None:
        """Find the latest open case grouping ``claim``.

        Args:
            claim: the claim text.

        Returns:
            The case or None.
        """
        async with await self._connect() as conn:
            cursor = await conn.execute(
                "SELECT body FROM moderator_cases"
                " WHERE state = 'open' AND body -> 'claims' @> %s"
                " ORDER BY last_seen DESC, id LIMIT 1",
                (Jsonb([{"claim": claim}]),),
            )
            row = await cursor.fetchone()
        return None if row is None else ModeratorCase.model_validate(row[0])

    async def list_cases(self, state: CaseState | None = None) -> list[ModeratorCase]:
        """List cases, latest first.

        Args:
            state: only cases in this state; all when None.

        Returns:
            The cases.
        """
        async with await self._connect() as conn:
            cursor = await conn.execute(
                "SELECT body FROM moderator_cases"
                " WHERE %(state)s::text IS NULL OR state = %(state)s"
                " ORDER BY last_seen DESC, id",
                {"state": state},
            )
            rows = await cursor.fetchall()
        return list(starmap(ModeratorCase.model_validate, rows))

    async def remove_checks(self, check_ids: Sequence[str]) -> None:
        """Drop the checks from every case; empty claims and cases go.

        Args:
            check_ids: the deleted checks.
        """
        async with await self._connect() as conn:
            await remove_case_checks(conn, check_ids)
