"""The publisher removals migration runs last among the corpus files and only adds."""

from importlib.resources import files

MIGRATIONS = files("meritum_core.corpus") / "migrations"
NAME = "0006_publisher_removals.sql"


def test_publisher_removals_migration_runs_after_the_documents_tables() -> None:
    names = sorted(f.name for f in MIGRATIONS.iterdir() if f.name.endswith(".sql"))
    assert names.index(NAME) > names.index("0003_corpus_documents.sql")


def test_publisher_removals_migration_only_adds_the_ledger_table() -> None:
    text = (MIGRATIONS / NAME).read_text(encoding="utf-8")
    sql = " ".join(line.split("--")[0] for line in text.splitlines()).upper()
    assert "CREATE TABLE IF NOT EXISTS CORPUS.PUBLISHER_REMOVALS" in sql
    assert not any(word in sql for word in ("DROP ", "DELETE ", "ALTER ", "TRUNCATE "))
