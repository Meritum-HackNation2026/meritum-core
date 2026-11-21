"""Corpus schema migrations on a real PostgreSQL: local only, ``uv run pytest -m integration``.

Needs the meritum-postgres image (pgvector, pg_trgm, ``public.polish``) and
``MERITUM_CORPUS_DATABASE_URL`` (like test_postgres_integration.py). The test drops
the EUvsDisinfo copy tables first, so it runs only while they hold no rows.
"""

import os
from importlib.resources import files

import psycopg
import pytest

MIGRATIONS = files("meritum_core.corpus") / "migrations"
COPY_ROWS = """
SELECT (SELECT count(*) FROM corpus.euvsdisinfo_entries)
     + (SELECT count(*) FROM corpus.euvsdisinfo_flagged_domains)
"""
DROP_COPY = """
DROP TABLE IF EXISTS corpus.euvsdisinfo_entries, corpus.euvsdisinfo_flagged_domains
"""
COLUMNS = """
SELECT table_name, column_name, format_type(atttypid, atttypmod), attnotnull
FROM information_schema.columns
JOIN pg_attribute ON attrelid = format('%I.%I', table_schema, table_name)::regclass
    AND attname = column_name
WHERE table_schema = 'corpus' AND table_name LIKE 'euvsdisinfo%'
ORDER BY table_name, ordinal_position
"""
EXPECTED = [
    ("euvsdisinfo_entries", "key", "text", True),
    ("euvsdisinfo_entries", "kind", "text", True),
    ("euvsdisinfo_entries", "entry", "jsonb", True),
    ("euvsdisinfo_entries", "description_embedding", "vector(768)", True),
    ("euvsdisinfo_entries", "fact_embedding", "vector(768)", False),
    ("euvsdisinfo_entries", "source", "jsonb", False),
    ("euvsdisinfo_entries", "deleted_at", "timestamp with time zone", False),
    ("euvsdisinfo_flagged_domains", "domain", "text", True),
    ("euvsdisinfo_flagged_domains", "case_keys", "text[]", True),
]


@pytest.mark.integration
def test_corpus_migrations_create_the_euvsdisinfo_copy_and_can_run_twice() -> None:
    url = os.environ.get("MERITUM_CORPUS_DATABASE_URL", "")
    if not url:
        pytest.skip("set MERITUM_CORPUS_DATABASE_URL to the meritum-postgres image")
    scripts = sorted(
        (f for f in MIGRATIONS.iterdir() if f.name.endswith(".sql")),
        key=lambda f: f.name,
    )
    with psycopg.connect(url, autocommit=True) as conn:
        conn.execute("CREATE SCHEMA IF NOT EXISTS corpus")  # the platform's job
        match conn.execute(
            "SELECT to_regclass('corpus.euvsdisinfo_entries')"
        ).fetchone():
            case (None,) | None:
                pass
            case _ if conn.execute(COPY_ROWS).fetchone() != (0,):
                pytest.skip("the EUvsDisinfo copy has rows; use an empty database")
            case _:
                conn.execute(DROP_COPY)
        for _ in range(2):
            for script in scripts:
                conn.execute(script.read_bytes())
        assert conn.execute(COLUMNS).fetchall() == EXPECTED
