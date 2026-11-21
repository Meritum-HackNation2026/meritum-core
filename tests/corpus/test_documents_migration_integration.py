"""Corpus documents, ingestion attempts and snapshot manifests: local only.

Needs the meritum-postgres image and ``MERITUM_CORPUS_DATABASE_URL`` (like
test_migrations_integration.py); runs every corpus migration twice and only
reads the catalogue of the three tables and their indexes, so it needs no
empty database.
"""

import os
from importlib.resources import files

import psycopg
import pytest

MIGRATIONS = files("meritum_core.corpus") / "migrations"
COLUMNS = """
SELECT table_name, column_name, format_type(atttypid, atttypmod), attnotnull
FROM information_schema.columns
JOIN pg_attribute ON attrelid = format('%I.%I', table_schema, table_name)::regclass
    AND attname = column_name
WHERE table_schema = 'corpus' AND table_name IN ('documents', 'ingest_attempts', 'snapshot_manifest')
ORDER BY table_name, ordinal_position
"""
INDEXES = """
SELECT indexname FROM pg_indexes
WHERE schemaname = 'corpus' AND indexname IN (
    'documents_fetched_at', 'documents_domain', 'passages_live_source_id'
)
ORDER BY indexname
"""
TIMESTAMP = "timestamp with time zone"
EXPECTED = [
    ("documents", "source_id", "text", True),
    ("documents", "url", "text", True),
    ("documents", "domain", "text", True),
    ("documents", "publisher_id", "text", True),
    ("documents", "license", "text", True),
    ("documents", "published_on", "date", False),
    ("documents", "fetched_at", TIMESTAMP, True),
    ("documents", "checksum", "text", True),
    ("documents", "full_text", "text", False),
    ("documents", "added_at", TIMESTAMP, True),
    ("documents", "retired_at", TIMESTAMP, False),
    ("ingest_attempts", "domain", "text", True),
    ("ingest_attempts", "attempted_at", TIMESTAMP, True),
    ("snapshot_manifest", "version", "text", True),
    ("snapshot_manifest", "source_id", "text", True),
    ("snapshot_manifest", "checksum", "text", True),
    ("snapshot_manifest", "fetched_at", TIMESTAMP, True),
]


@pytest.mark.integration
def test_corpus_migrations_create_documents_attempts_and_snapshot_manifest() -> None:
    url = os.environ.get("MERITUM_CORPUS_DATABASE_URL", "")
    if not url:
        pytest.skip("set MERITUM_CORPUS_DATABASE_URL to the meritum-postgres image")
    scripts = sorted(
        (f for f in MIGRATIONS.iterdir() if f.name.endswith(".sql")),
        key=lambda f: f.name,
    )
    with psycopg.connect(url, autocommit=True) as conn:
        for _ in range(2):
            for script in scripts:
                conn.execute(script.read_bytes())
        assert conn.execute(COLUMNS).fetchall() == EXPECTED
        assert conn.execute(INDEXES).fetchall() == [
            ("documents_domain",),
            ("documents_fetched_at",),
            ("passages_live_source_id",),
        ]
