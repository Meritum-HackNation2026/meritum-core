"""Fixtures shared by the PostgreSQL integration tests (local only, ``-m integration``)."""

import os
import uuid
from collections.abc import Iterator

import psycopg
import pytest
from psycopg import sql
from psycopg.conninfo import make_conninfo

from meritum_core.shared.database.adapters import apply_migrations


@pytest.fixture
def app_database_url() -> Iterator[str]:
    """A fresh, migrated schema of its own; yields a URL whose search_path names it.

    Needs ``MERITUM_TEST_DATABASE_URL`` pointing at a PostgreSQL the user may create
    schemas in (the meritum-postgres image from meritum-infra, or plain postgres).
    """
    admin = os.environ.get("MERITUM_TEST_DATABASE_URL", "")
    if not admin:
        pytest.skip("set MERITUM_TEST_DATABASE_URL to a local PostgreSQL")
    schema = f"test_{uuid.uuid4().hex}"
    with psycopg.connect(admin, autocommit=True) as conn:
        conn.execute(sql.SQL("CREATE SCHEMA {}").format(sql.Identifier(schema)))
    url = make_conninfo(admin, options=f"-c search_path={schema}")
    apply_migrations(url)
    yield url
    with psycopg.connect(admin, autocommit=True) as conn:
        conn.execute(sql.SQL("DROP SCHEMA {} CASCADE").format(sql.Identifier(schema)))
