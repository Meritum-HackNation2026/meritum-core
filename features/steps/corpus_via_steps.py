"""Steps for the via column scenario in features/corpus.feature.

CI has no database, so the steps read the migration's SQL; the integration test
tests/corpus/test_documents_migration_integration.py applies it to PostgreSQL.

Features:
    US-KOR-03, F-13
"""

import re
from importlib.resources import files
from typing import get_args

from behave import given, then, when
from behave.runner import Context

from meritum_core.checks.contracts import SourceVia


@given("migracja corpus {name}")
def given_migration(context: Context, name: str) -> None:
    """Read the named corpus migration."""
    context.via_sql = (files("meritum_core.corpus") / "migrations" / name).read_text(
        encoding="utf-8"
    )


@when("sprawdzam kolumnę via w corpus.documents")
def when_check_via(context: Context) -> None:
    """Pull the CHECK values and the default of via out of the SQL."""
    sql = context.via_sql
    check = re.search(r"CHECK \(via IN \(([^)]*)\)\)", sql)
    default = re.search(
        r"ADD COLUMN IF NOT EXISTS via text NOT NULL DEFAULT '(\w+)'", sql
    )
    assert check is not None
    assert default is not None
    context.via_allowed = {v.strip().strip("'") for v in check.group(1).split(",")}
    context.via_default = default.group(1)


@then(
    'dopuszcza dokładnie wartości SourceVia, w tym "{value}", '
    'a dokumenty sprzed migracji mają via = "{default}"'
)
def then_via_matches_contract(context: Context, value: str, default: str) -> None:
    """Compare the column with the SourceVia literal."""
    assert context.via_allowed == set(get_args(SourceVia))
    assert value in context.via_allowed
    assert context.via_default == default
