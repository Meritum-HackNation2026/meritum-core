"""In-memory CheckRecordRepository for the tests of meritum-backend and meritum-worker.

Features:
    US-OBS-01, US-BEZ-05, F-22, F-24
"""

from collections.abc import Sequence
from datetime import datetime

from meritum_core.checks.contracts import CheckRecord
from meritum_core.checks.ports import SubjectKind


class InMemoryCheckRecordRepository:
    """CheckRecordRepository fake that keeps the records in a dict.

    Features:
        US-OBS-01, US-BEZ-05, F-22, F-24
    """

    def __init__(self) -> None:
        self._records: dict[str, CheckRecord] = {}

    async def save(self, record: CheckRecord) -> None:
        """Store ``record`` under its ``check_id``.

        Args:
            record: the record to store.
        """
        self._records[record.check_id] = record

    async def get(self, check_id: str) -> CheckRecord | None:
        """Read one record.

        Args:
            check_id: the check's id.

        Returns:
            The record or None.
        """
        return self._records.get(check_id)

    async def list_for(self, kind: SubjectKind, value: str) -> list[CheckRecord]:
        """List one person's records, newest first.

        Args:
            kind: which field names the person.
            value: its value.

        Returns:
            The matching records.
        """
        found = [r for r in self._records.values() if getattr(r, kind) == value]
        return sorted(found, key=lambda r: r.received_at, reverse=True)

    async def delete_subject(self, kind: SubjectKind, value: str) -> list[str]:
        """Delete one person's records.

        Args:
            kind: which field names the person.
            value: its value.

        Returns:
            The deleted check ids.
        """
        ids = [r.check_id for r in await self.list_for(kind, value)]
        await self.delete(ids)
        return ids

    async def expired(self, now: datetime, *, limit: int) -> list[str]:
        """Select records past retention, oldest first.

        Args:
            now: the retention run's time.
            limit: the most ids to return.

        Returns:
            The expired check ids.
        """
        due = [r for r in self._records.values() if r.retention_until <= now]
        due.sort(key=lambda r: r.retention_until)
        return [r.check_id for r in due[:limit]]

    async def delete(self, check_ids: Sequence[str]) -> None:
        """Delete the given records, ignoring unknown ids.

        Args:
            check_ids: the records to delete.
        """
        for check_id in check_ids:
            self._records.pop(check_id, None)
