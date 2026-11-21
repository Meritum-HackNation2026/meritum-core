"""Corpus migrations as the platform's schema owner: local only, ``-m integration``.

Needs the meritum-postgres image and ``MERITUM_CORPUS_DATABASE_URL`` as a superuser.
The test copies that database, sets up a role and the ``corpus`` schema the way
meritum-infra's ``db.sh`` does (the role owns ``corpus`` and has only ``CONNECT``
on the database), then applies every corpus migration as that role.
"""

import os
import uuid
from collections.abc import Iterator
from importlib.resources import files

import psycopg
import pytest
from psycopg import sql
from psycopg.conninfo import make_conninfo

MIGRATIONS = files("meritum_core.corpus") / "migrations"
TABLES = (
    "SELECT table_name FROM information_schema.tables WHERE table_schema = 'corpus'"
)


def run(conninfo: str, *queries: sql.SQL | sql.Composed) -> None:
    with psycopg.connect(conninfo, autocommit=True) as conn:
        for query in queries:
            conn.execute(query)


@pytest.fixture
def owner_url() -> Iterator[str]:
    """A copy of the database with ``corpus`` owned by a CONNECT-only role; its URL."""
    admin = os.environ.get("MERITUM_CORPUS_DATABASE_URL", "")
    if not admin:
        pytest.skip("set MERITUM_CORPUS_DATABASE_URL to the meritum-postgres image")
    name, password = f"corpus_test_{uuid.uuid4().hex}", uuid.uuid4().hex
    db = role = sql.Identifier(name)  # one name for the copied database and its role
    with psycopg.connect(admin) as conn:
        source = sql.Identifier(conn.info.dbname)
    maintenance = make_conninfo(admin, dbname="postgres")
    url = make_conninfo(admin, dbname=name)
    try:
        run(
            maintenance,
            sql.SQL("CREATE DATABASE {} TEMPLATE {}").format(db, source),
            sql.SQL("CREATE ROLE {} LOGIN PASSWORD {}").format(role, password),
        )
        # The same grants as db.sh: no CREATE on the database, owner of corpus.
        run(
            url,
            sql.SQL("REVOKE ALL ON DATABASE {} FROM PUBLIC").format(db),
            sql.SQL("GRANT CONNECT ON DATABASE {} TO {}").format(db, role),
            sql.SQL("DROP SCHEMA IF EXISTS corpus CASCADE"),
            sql.SQL("CREATE SCHEMA corpus AUTHORIZATION {}").format(role),
        )
        yield make_conninfo(url, user=name, password=password)
    finally:
        run(
            maintenance,
            sql.SQL("DROP DATABASE IF EXISTS {} WITH (FORCE)").format(db),
            sql.SQL("DROP ROLE IF EXISTS {}").format(role),
        )


@pytest.mark.integration
def test_issue_scenario_migrations_run_as_the_corpus_schema_owner(
    owner_url: str,
) -> None:
    scripts = sorted(
        (f for f in MIGRATIONS.iterdir() if f.name.endswith(".sql")),
        key=lambda f: f.name,
    )
    with psycopg.connect(owner_url, autocommit=True) as conn:
        for script in scripts:
            conn.execute(script.read_bytes())
        tables = {row[0] for row in conn.execute(TABLES).fetchall()}
    assert {"passages", "snapshots"} <= tables
