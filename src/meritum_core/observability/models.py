"""Models of the observability slice.

Features:
    US-OBS-01, US-MOD-01, US-BEZ-05, F-22, F-24
"""

from dataclasses import dataclass

from meritum_core.checks import CheckRecordRepository
from meritum_core.moderation import HighRiskTopicRepository, ModeratorCaseRepository
from meritum_core.notifications import NotificationRepository
from meritum_core.observability.ports import SubjectEraser


@dataclass(frozen=True)
class AppRepositories:
    """Every repository of the app schema, all over the same store.

    Attributes:
        records: the check records.
        cases: the moderator cases.
        topics: the high-risk topic list.
        notifications: the inbox notifications.
        eraser: erases one person from all of them in one go.

    Features:
        US-OBS-01, US-MOD-01, US-BEZ-05, F-22, F-24
    """

    records: CheckRecordRepository
    cases: ModeratorCaseRepository
    topics: HighRiskTopicRepository
    notifications: NotificationRepository
    eraser: SubjectEraser
