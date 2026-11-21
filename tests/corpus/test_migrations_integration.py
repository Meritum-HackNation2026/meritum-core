"""Corpus schema migrations on a real PostgreSQL: local only, ``uv run pytest -m integration``.

Needs the meritum-postgres image (pgvector, pg_trgm, ``public.polish``) and
``MERITUM_TEST_DATABASE_URL``; the migrations only add, so rerunning them is safe.
"""

import os
from importlib.resources import files

import psycopg
import pytest

MIGRATIONS = files("meritum_core.corpus") / "migrations"
TABLES = """
SELECT table_name FROM information_schema.tables WHERE table_schema = 'corpus'
"""


@pytest.mark.integration
def test_corpus_migrations_create_the_euvsdisinfo_copy_and_can_run_twice() -> None:
    url = os.environ.get("MERITUM_TEST_DATABASE_URL", "")
    if not url:
        pytest.skip("set MERITUM_TEST_DATABASE_URL to the meritum-postgres image")
    scripts = sorted(
        (f for f in MIGRATIONS.iterdir() if f.name.endswith(".sql")),
        key=lambda f: f.name,
    )
    with psycopg.connect(url, autocommit=True) as conn:
        for _ in range(2):
            for script in scripts:
                conn.execute(script.read_bytes())
        found = {name for (name,) in conn.execute(TABLES).fetchall()}
    assert {"euvsdisinfo_entries", "euvsdisinfo_flagged_domains"} <= found
