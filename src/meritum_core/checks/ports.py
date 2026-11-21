"""Ports of the checks slice: where check records are kept.

Features:
    US-OBS-01, US-BEZ-05, F-22, F-24, ADR-13
"""

from collections.abc import Sequence
from datetime import datetime
from typing import Literal, Protocol

from meritum_core.checks.contracts import CheckRecord

type SubjectKind = Literal["session_id", "user_id", "channel_user_hash"]
"""The CheckRecord field that names a person, as in `DeleteSubjectInput.kind`."""


class CheckRecordRepository(Protocol):
    """Stores the audit record of every check (port).

    The worker saves records, the backend reads them (result, history, deletion,
    export). Every adapter passes the contract test in ``tests/checks/records/``.

    Features:
        US-OBS-01, US-BEZ-05, F-22, F-24, ADR-13
    """

    async def save(self, record: CheckRecord) -> None:
        """Store ``record``, replacing a stored one with the same ``check_id``.

        Replacing keeps a retried workflow step idempotent.

        Args:
            record: the record to store.
        """
        ...

    async def get(self, check_id: str) -> CheckRecord | None:
        """Read one record.

        Args:
            check_id: the check's id.

        Returns:
            The stored record, or None when there is none.
        """
        ...

    async def list_for(self, kind: SubjectKind, value: str) -> list[CheckRecord]:
        """List one person's records, newest ``received_at`` first.

        Args:
            kind: which field names the person (a session or an account).
            value: the session id, user id or channel user hash.

        Returns:
            The matching records.
        """
        ...

    async def delete_subject(self, kind: SubjectKind, value: str) -> list[str]:
        """Delete every record of one person (US-BEZ-05).

        Args:
            kind: which field names the person.
            value: the session id, user id or channel user hash.

        Returns:
            The ``check_id`` of each deleted record, so moderator cases can drop them.
        """
        ...

    async def expired(self, now: datetime, *, limit: int) -> list[str]:
        """Select records whose ``retention_until`` has passed, oldest first (ADR-13).

        Args:
            now: the retention run's time.
            limit: the most ids to return in one batch.

        Returns:
            The ``check_id`` of each expired record.
        """
        ...

    async def delete(self, check_ids: Sequence[str]) -> None:
        """Delete the given records; unknown ids are ignored.

        Args:
            check_ids: the records to delete.
        """
        ...
