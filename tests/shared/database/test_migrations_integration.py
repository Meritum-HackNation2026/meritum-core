"""App schema migrations on a real PostgreSQL: local only, ``uv run pytest -m integration``."""

import os
import uuid
from collections.abc import Iterator
from importlib.resources import files

import psycopg
import pytest
from psycopg import sql
from psycopg.conninfo import make_conninfo

from meritum_core.shared.database.adapters import apply_migrations, main

APP_TABLES = {
    "check_records",
    "moderator_cases",
    "high_risk_topics",
    "notifications",
    "removed_case_checks",
    "staff_accounts",
    "result_cache",
    "result_cache_checks",
    "jury_links",
    "rate_limit_hits",
    "eval_runs",
    "eval_datasets",
    "page_archives",
    "schema_migrations",
}
MIGRATIONS = sorted(
    f.name
    for f in (files("meritum_core.shared.database") / "migrations").iterdir()
    if f.name.endswith(".sql")
)
LIST_TABLES = "SELECT table_name FROM information_schema.tables WHERE table_schema = %s"
SNAPSHOT = """
SELECT table_name, column_name, data_type FROM information_schema.columns
WHERE table_schema = %s ORDER BY table_name, column_name
"""


@pytest.fixture
def empty_schema() -> Iterator[tuple[str, str]]:
    """An empty schema; yields (its URL with search_path, its name)."""
    admin = os.environ.get("MERITUM_TEST_DATABASE_URL", "")
    if not admin:
        pytest.skip("set MERITUM_TEST_DATABASE_URL to a local PostgreSQL")
    schema = f"app_test_{uuid.uuid4().hex}"
    with psycopg.connect(admin, autocommit=True) as conn:
        conn.execute(sql.SQL("CREATE SCHEMA {}").format(sql.Identifier(schema)))
    yield make_conninfo(admin, options=f"-c search_path={schema}"), schema
    with psycopg.connect(admin, autocommit=True) as conn:
        conn.execute(sql.SQL("DROP SCHEMA {} CASCADE").format(sql.Identifier(schema)))


def columns(url: str, schema: str) -> list[str]:
    with psycopg.connect(url) as conn:
        return [repr(row) for row in conn.execute(SNAPSHOT, (schema,)).fetchall()]


@pytest.mark.integration
def test_issue_scenario_migrations_on_an_empty_schema(
    empty_schema: tuple[str, str],
) -> None:
    url, schema = empty_schema
    assert apply_migrations(url) == MIGRATIONS
    with psycopg.connect(url) as conn:
        tables = {row[0] for row in conn.execute(LIST_TABLES, (schema,)).fetchall()}
    assert tables == APP_TABLES
    before = columns(url, schema)
    assert apply_migrations(url) == []
    assert columns(url, schema) == before


@pytest.mark.integration
def test_missing_search_path_schema_is_an_error() -> None:
    admin = os.environ.get("MERITUM_TEST_DATABASE_URL", "")
    if not admin:
        pytest.skip("set MERITUM_TEST_DATABASE_URL to a local PostgreSQL")
    url = make_conninfo(admin, options=f"-c search_path=missing_{uuid.uuid4().hex}")
    with pytest.raises(RuntimeError, match="search_path"):
        apply_migrations(url)


@pytest.mark.integration
def test_issue_scenario_the_deploy_command_migrates_once(
    empty_schema: tuple[str, str],
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    url, _ = empty_schema
    monkeypatch.setenv("MERITUM_DATABASE_URL", url)
    main()
    main()
    assert capsys.readouterr().out.splitlines() == [
        f"applied: {', '.join(MIGRATIONS)}",
        "applied: nothing",
    ]


@pytest.mark.integration
def test_notifications_are_indexed_by_check_id(empty_schema: tuple[str, str]) -> None:
    url, schema = empty_schema
    apply_migrations(url)
    with psycopg.connect(url) as conn:
        row = conn.execute(
            "SELECT indexdef FROM pg_indexes WHERE schemaname = %s"
            " AND indexname = 'notifications_check_id'",
            (schema,),
        ).fetchone()
    assert row is not None
    assert "check_id" in str(row[0])


@pytest.mark.integration
def test_rate_limit_hits_are_indexed_by_window_start(
    empty_schema: tuple[str, str],
) -> None:
    url, schema = empty_schema
    apply_migrations(url)
    with psycopg.connect(url) as conn:
        row = conn.execute(
            "SELECT indexdef FROM pg_indexes WHERE schemaname = %s"
            " AND indexname = 'rate_limit_hits_window_start'",
            (schema,),
        ).fetchone()
    assert row is not None
    assert "window_start" in str(row[0])
