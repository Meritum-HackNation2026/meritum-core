"""Builds the app repositories named by ``MERITUM_DATABASE_PROVIDER``.

Features:
    US-OBS-01, US-MOD-01, US-MOD-05, US-BEZ-05, F-22, F-24, F-25, ADR-04
"""

from meritum_core.checks.adapters import PostgresCheckRecordRepository
from meritum_core.checks.fakes import InMemoryCheckRecordRepository
from meritum_core.moderation.adapters import (
    PostgresHighRiskTopicRepository,
    PostgresModeratorCaseRepository,
    PostgresStaffRepository,
)
from meritum_core.moderation.fakes import (
    InMemoryHighRiskTopicRepository,
    InMemoryModeratorCaseRepository,
    InMemoryStaffRepository,
)
from meritum_core.notifications.adapters import PostgresNotificationRepository
from meritum_core.notifications.fakes import InMemoryNotificationRepository
from meritum_core.observability.adapters import PostgresSubjectEraser
from meritum_core.observability.fakes import InMemorySubjectEraser
from meritum_core.observability.models import AppRepositories
from meritum_core.shared.database import DatabaseProvider, DatabaseSettings


def build_app_repositories(settings: DatabaseSettings) -> AppRepositories:
    """Build every app repository over the store the settings name.

    Args:
        settings: Usually ``DatabaseSettings()`` from the environment.

    Returns:
        The in-memory fakes (sharing their data with the eraser) or the
        PostgreSQL adapters over the schema of ``MERITUM_DATABASE_URL``.

    Raises:
        ValueError: postgres without a database URL (settings built unvalidated).

    Features:
        US-OBS-01, US-MOD-01, US-MOD-05, US-BEZ-05, F-22, F-24, F-25, ADR-04
    """
    match settings.provider:
        case DatabaseProvider.POSTGRES:
            if settings.url is None:
                msg = "MERITUM_DATABASE_URL is required for postgres"
                raise ValueError(msg)
            url = settings.url.get_secret_value()
            return AppRepositories(
                records=PostgresCheckRecordRepository(url),
                cases=PostgresModeratorCaseRepository(url),
                topics=PostgresHighRiskTopicRepository(url),
                staff=PostgresStaffRepository(url),
                notifications=PostgresNotificationRepository(url),
                eraser=PostgresSubjectEraser(url),
            )
        case DatabaseProvider.MEMORY:
            records = InMemoryCheckRecordRepository()
            cases = InMemoryModeratorCaseRepository()
            notifications = InMemoryNotificationRepository()
            return AppRepositories(
                records=records,
                cases=cases,
                topics=InMemoryHighRiskTopicRepository(),
                staff=InMemoryStaffRepository(),
                notifications=notifications,
                eraser=InMemorySubjectEraser(records, cases, notifications),
            )
