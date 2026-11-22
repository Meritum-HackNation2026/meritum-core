"""Migration 0007 lets corpus.documents keep only the values of SourceVia.

Features:
    US-KOR-03, F-13
"""

import re
from importlib.resources import files
from typing import get_args

from meritum_core.checks.contracts import SourceVia

MIGRATION = files("meritum_core.corpus") / "migrations" / "0007_documents_via.sql"


def _sql() -> str:
    return MIGRATION.read_text(encoding="utf-8")


def test_via_column_defaults_to_the_contract_default() -> None:
    assert r"ADD COLUMN IF NOT EXISTS via text NOT NULL DEFAULT 'corpus'" in _sql()


def test_via_check_allows_exactly_the_source_via_values() -> None:
    match = re.search(r"CHECK \(via IN \(([^)]*)\)\)", _sql())
    assert match is not None
    allowed = {v.strip().strip("'") for v in match.group(1).split(",")}
    assert allowed == set(get_args(SourceVia))
