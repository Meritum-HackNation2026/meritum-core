"""Applies the app schema's SQL migrations once each, in file-name order.

Features:
    US-OBS-01, US-BEZ-05, F-22, ADR-03, ADR-04
"""

import sys
from importlib.resources import files

import psycopg

from meritum_core.shared.database.constants import (
    MIGRATION_SUFFIX,
    MIGRATIONS_DIRECTORY,
    MIGRATIONS_LOCK,
    MIGRATIONS_PACKAGE,
)
from meritum_core.shared.database.settings import DatabaseProvider, DatabaseSettings


def apply_migrations(conninfo: str) -> list[str]:
    """Apply the migrations not yet recorded in ``schema_migrations``.

    Everything runs in one transaction under an advisory lock, so a failed file
    leaves the schema as it was and two deploys never migrate at once.

    Args:
        conninfo: libpq connection string; its ``search_path`` names the schema.

    Returns:
        The file names applied by this run; empty when the schema is up to date.

    Raises:
        RuntimeError: the ``search_path`` names no existing schema.

    Features:
        US-OBS-01, US-BEZ-05, F-22, ADR-03, ADR-04
    """
    directory = files(MIGRATIONS_PACKAGE) / MIGRATIONS_DIRECTORY
    scripts = sorted(
        (f for f in directory.iterdir() if f.name.endswith(MIGRATION_SUFFIX)),
        key=lambda f: f.name,
    )
    with psycopg.connect(conninfo) as conn, conn.transaction():
        conn.execute("SELECT pg_advisory_xact_lock(%s)", (MIGRATIONS_LOCK,))
        match conn.execute("SELECT current_schema()").fetchone():
            case (str(),):
                pass
            case _:
                msg = "the connection's search_path names no existing schema"
                raise RuntimeError(msg)
        conn.execute(
            "CREATE TABLE IF NOT EXISTS schema_migrations ("
            " name text PRIMARY KEY, applied_at timestamptz NOT NULL DEFAULT now())"
        )
        rows = conn.execute("SELECT name FROM schema_migrations").fetchall()
        done = {name for (name,) in rows}
        applied = [s for s in scripts if s.name not in done]
        for script in applied:
            conn.execute(script.read_bytes())
            conn.execute(
                "INSERT INTO schema_migrations (name) VALUES (%s)", (script.name,)
            )
    return [s.name for s in applied]


def main() -> None:
    """Migrate the schema named by ``MERITUM_DATABASE_URL`` (``meritum-migrate-app``).

    The worker's deploy runs it before the new version starts (worker/035).

    Features:
        US-OBS-01, F-22, ADR-03
    """
    settings = DatabaseSettings(provider=DatabaseProvider.POSTGRES)
    url = settings.url
    if url is None:  # the settings validator already refuses this
        sys.exit("MERITUM_DATABASE_URL is required")
    applied = apply_migrations(url.get_secret_value())
    sys.stdout.write(f"applied: {', '.join(applied) or 'nothing'}\n")
