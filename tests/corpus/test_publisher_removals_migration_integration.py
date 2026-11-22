"""Ledger of publisher removal requests in the corpus schema: local only.

Needs the meritum-postgres image and ``MERITUM_CORPUS_DATABASE_URL`` (like
test_documents_migration_integration.py); runs every corpus migration twice,
records one request inside a rolled-back transaction and leaves no rows behind.
"""

import os
from datetime import UTC, datetime, timedelta
from importlib.resources import files

import psycopg
import pytest

MIGRATIONS = files("meritum_core.corpus") / "migrations"
INSERT = """
INSERT INTO corpus.publisher_removals
    (url, publisher_id, requested_at, removed_at, documents)
VALUES (%s, %s, %s, %s, %s)
"""
SELECT = """
SELECT url, publisher_id, requested_at, removed_at, documents
FROM corpus.publisher_removals WHERE url = %s
"""


@pytest.mark.integration
def test_issue_scenario_publisher_removal_is_recorded_after_migrations() -> None:
    url = os.environ.get("MERITUM_CORPUS_DATABASE_URL", "")
    if not url:
        pytest.skip("set MERITUM_CORPUS_DATABASE_URL to the meritum-postgres image")
    scripts = sorted(
        (f for f in MIGRATIONS.iterdir() if f.name.endswith(".sql")),
        key=lambda f: f.name,
    )
    requested = datetime(2026, 11, 20, 9, 0, tzinfo=UTC)
    removed = requested + timedelta(days=1)
    row = ("https://example.org/a", "example-publisher", requested, removed, 2)
    with psycopg.connect(url, autocommit=True) as conn:
        conn.execute("CREATE SCHEMA IF NOT EXISTS corpus")  # the platform's job
        for _ in range(2):
            for script in scripts:
                conn.execute(script.read_bytes())
    with psycopg.connect(url) as conn:
        conn.execute(INSERT, row)
        assert conn.execute(SELECT, (row[0],)).fetchall() == [row]
        with pytest.raises(psycopg.errors.CheckViolation):
            conn.execute(INSERT, (*row[:2], removed, removed, -1))
        conn.rollback()
