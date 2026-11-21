"""Constants of the app database.

Features:
    US-OBS-01, US-BEZ-05, F-22, ADR-04
"""

from typing import Final

ENV_PREFIX: Final = "MERITUM_DATABASE_"
"""Prefix of every app database setting (``MERITUM_DATABASE_URL`` from infra#12)."""

MIGRATIONS_PACKAGE: Final = "meritum_core.shared.database"
"""Package whose ``migrations/`` directory holds the app schema's SQL files."""

MIGRATIONS_DIRECTORY: Final = "migrations"
"""Directory of ``MIGRATIONS_PACKAGE`` with the SQL files, applied in name order."""

MIGRATION_SUFFIX: Final = ".sql"
"""Suffix of a migration file; other files in the directory are ignored."""

MIGRATIONS_LOCK: Final = 38_0001
"""Advisory lock key: two deploys migrating at once run one after the other."""
