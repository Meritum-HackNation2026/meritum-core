"""Applies the corpus_ready migrations once each, in file-name order.

Features:
    US-KOR-02, F-12
"""

from importlib.resources import files

import psycopg

from meritum_core.corpus.ready.constants import (
    READY_MIGRATION_SUFFIX,
    READY_MIGRATIONS_LOCK,
)


def apply_corpus_ready_migrations(conninfo: str) -> list[str]:
    """Apply the ``ready/migrations`` files not yet recorded as applied.

    Called only by the worker's gold build with ``MERITUM_CORPUS_READY`` on, never
    by a deploy: a missing ``corpus_ready`` schema fails that build and nothing else.
    One transaction under an advisory lock, so a failed file changes nothing.

    Args:
        conninfo: libpq connection string of the role that owns ``corpus_ready``.

    Returns:
        The file names applied by this run; empty when up to date.

    Raises:
        RuntimeError: A migration failed; the message starts with its file name.

    Features:
        US-KOR-02, F-12
    """
    directory = files("meritum_core.corpus.ready") / "migrations"
    scripts = sorted(
        (f for f in directory.iterdir() if f.name.endswith(READY_MIGRATION_SUFFIX)),
        key=lambda f: f.name,
    )
    with psycopg.connect(conninfo) as conn, conn.transaction():
        conn.execute("SELECT pg_advisory_xact_lock(%s)", (READY_MIGRATIONS_LOCK,))
        conn.execute(
            "CREATE TABLE IF NOT EXISTS corpus_ready.schema_migrations ("
            " name text PRIMARY KEY, applied_at timestamptz NOT NULL DEFAULT now())"
        )
        rows = conn.execute("SELECT name FROM corpus_ready.schema_migrations")
        done = {name for (name,) in rows.fetchall()}
        applied = [s for s in scripts if s.name not in done]
        for script in applied:
            try:
                conn.execute(script.read_bytes())
            except psycopg.Error as exc:
                msg = f"{script.name}: {exc}"
                raise RuntimeError(msg) from exc
            conn.execute(
                "INSERT INTO corpus_ready.schema_migrations (name) VALUES (%s)",
                (script.name,),
            )
    return [s.name for s in applied]
