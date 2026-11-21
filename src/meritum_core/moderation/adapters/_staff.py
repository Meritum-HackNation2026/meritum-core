"""PostgreSQL StaffRepository over the ``staff_accounts`` table.

Features:
    US-MOD-05, F-25
"""

from psycopg import AsyncConnection

from meritum_core.checks.contracts import StaffRole
from meritum_core.moderation.models import StaffAccount


class PostgresStaffRepository:
    """StaffRepository that keeps each account as a row (see the port).

    Args:
        conninfo: libpq connection string; its ``search_path`` names the app schema.

    Features:
        US-MOD-05, F-25
    """

    def __init__(self, conninfo: str) -> None:
        self._conninfo = conninfo

    async def _connect(self) -> AsyncConnection:
        # shortcut: one connection per call; the staff gate reads one row per request.
        return await AsyncConnection.connect(self._conninfo)

    async def list_accounts(self) -> list[StaffAccount]:
        """List every account, sorted by address in code point order.

        Returns:
            The accounts.
        """
        async with await self._connect() as conn:
            cursor = await conn.execute(
                'SELECT email, role FROM staff_accounts ORDER BY email COLLATE "C"'
            )
            rows = await cursor.fetchall()
        return [StaffAccount(email=email, role=role) for email, role in rows]

    async def save_account(self, account: StaffAccount) -> None:
        """Grant a role, replacing the previous one.

        Args:
            account: the address and its role.
        """
        async with await self._connect() as conn:
            await conn.execute(
                "INSERT INTO staff_accounts (email, role) VALUES (%s, %s)"
                " ON CONFLICT (email) DO UPDATE SET role = EXCLUDED.role",
                (account.email, account.role),
            )

    async def delete_account(self, email: str) -> None:
        """Take the role away, if any.

        Args:
            email: the lower-cased address.
        """
        async with await self._connect() as conn:
            await conn.execute("DELETE FROM staff_accounts WHERE email = %s", (email,))

    async def role(self, email: str) -> StaffRole | None:
        """Read the role granted to an address.

        Args:
            email: the lower-cased address.

        Returns:
            The role or None.
        """
        async with await self._connect() as conn:
            cursor = await conn.execute(
                "SELECT role FROM staff_accounts WHERE email = %s", (email,)
            )
            row = await cursor.fetchone()
        return None if row is None else StaffAccount(email=email, role=row[0]).role
