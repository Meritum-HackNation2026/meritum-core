"""Ports of the observability slice: erasing one person from every app table.

Features:
    US-BEZ-05, F-24, ADR-13
"""

from typing import Protocol

from meritum_core.checks import SubjectKind


class SubjectEraser(Protocol):
    """Erases one person's data from every app table at once (port, US-BEZ-05).

    Deletes their check records, their notifications and the notifications about
    their checks, and drops their checks from moderator cases. Every adapter
    passes the contract test in ``tests/observability/``.

    Features:
        US-BEZ-05, F-24, ADR-13
    """

    async def erase(self, kind: SubjectKind, value: str) -> int:
        """Erase everything stored about one person, all or nothing.

        Args:
            kind: which identifier names the person.
            value: the session id, user id or channel user hash.

        Returns:
            How many check records and notifications were deleted.
        """
        ...
