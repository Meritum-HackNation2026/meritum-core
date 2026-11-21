"""In-memory SubjectEraser over the in-memory repositories, for tests and local runs.

Features:
    US-BEZ-05, F-24
"""

from meritum_core.checks import CheckRecordRepository, SubjectKind
from meritum_core.moderation import ModeratorCaseRepository
from meritum_core.notifications import NotificationRepository
from meritum_core.observability.constants import SUBJECT_RECIPIENT


class InMemorySubjectEraser:
    """SubjectEraser fake that calls the repositories one after another.

    Args:
        records: the check records.
        cases: the moderator cases.
        notifications: the inbox notifications.

    Features:
        US-BEZ-05, F-24
    """

    def __init__(
        self,
        records: CheckRecordRepository,
        cases: ModeratorCaseRepository,
        notifications: NotificationRepository,
    ) -> None:
        self._records = records
        self._cases = cases
        self._notifications = notifications

    async def erase(self, kind: SubjectKind, value: str) -> int:
        """Erase one person's records, notifications and case checks.

        Args:
            kind: which identifier names the person.
            value: its value.

        Returns:
            How many records and notifications were deleted.
        """
        check_ids = await self._records.delete_subject(kind, value)
        await self._cases.remove_checks(check_ids)
        notes = await self._notifications.delete_for(SUBJECT_RECIPIENT[kind], value)
        notes += await self._notifications.delete_for_checks(check_ids)
        return len(check_ids) + notes
