"""Migration 0010 adds the legal act metadata table next to corpus.documents.

Features:
    US-KOR-02, F-12
"""

import re
from importlib.resources import files

from meritum_core.corpus import LegalActMeta

MIGRATIONS = files("meritum_core.corpus") / "migrations"
NAME = "0010_document_legal_meta.sql"


def _sql() -> str:
    text = (MIGRATIONS / NAME).read_text(encoding="utf-8")
    return "\n".join(line.split("--")[0] for line in text.splitlines())


def test_legal_meta_migration_runs_after_the_documents_table() -> None:
    names = sorted(f.name for f in MIGRATIONS.iterdir() if f.name.endswith(".sql"))
    assert names[-1] == NAME
    assert names.index(NAME) > names.index("0003_corpus_documents.sql")


def test_legal_meta_migration_only_adds_a_table() -> None:
    sql = " ".join(_sql().split()).upper().replace("ON DELETE CASCADE", "")
    assert "CREATE TABLE IF NOT EXISTS CORPUS.DOCUMENT_LEGAL_META" in sql
    assert not any(word in sql for word in ("DROP ", "DELETE ", "ALTER ", "TRUNCATE "))


def test_legal_meta_rows_go_with_their_document() -> None:
    sql = " ".join(_sql().split())
    assert "REFERENCES corpus.documents (source_id) ON DELETE CASCADE" in sql


def test_legal_meta_columns_are_the_fields_agreed_on_worker_162() -> None:
    body = _sql().split("(", 1)[1]
    columns = re.findall(r"^\s{4}([a-z_]+) ", body, flags=re.MULTILINE)
    assert columns == [
        "source_id",
        "eli",
        "document_type",
        "legal_status",
        "in_force",
        "in_force_from",
        "in_force_until",
        "journal_publisher",
        "journal_year",
        "journal_position",
        "display_address",
        "updated_at",
    ]
    assert columns[1:-1] == list(LegalActMeta.model_fields)
