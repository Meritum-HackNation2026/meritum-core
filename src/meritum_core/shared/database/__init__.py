"""App database: where the check, case, topic and notification tables live.

Public API of the concept: re-exports only. The PostgreSQL migrations and their
runner (``meritum-migrate-app``) are in ``meritum_core.shared.database.adapters``.

Features:
    US-OBS-01, US-MOD-01, US-BEZ-05, F-22, F-24, ADR-04
"""

from meritum_core.shared.database.settings import DatabaseProvider, DatabaseSettings

__all__ = ["DatabaseProvider", "DatabaseSettings"]
