"""corpus_ready migration, rollback and gold search on a real database.

Local only: ``uv run pytest -m integration`` with ``MERITUM_CORPUS_DATABASE_URL``
pointing at the meritum-postgres image. The test creates both schemas (the
platform's job), applies the migrations and drops what it created.
"""

import asyncio
import os
from collections.abc import Iterator
from datetime import UTC, date, datetime
from importlib.resources import files

import psycopg
import pytest

from meritum_core.corpus import CorpusSettings, build_corpus_search
from meritum_core.corpus.ready.adapters import apply_corpus_ready_migrations
from meritum_core.shared.embeddings import EmbeddingsSettings, build_embeddings

TAKEN_AT = datetime(2026, 11, 21, 12, tzinfo=UTC)
FULL_TEXT = (
    "Konstytucja Rzeczypospolitej Polskiej\n\n"
    "Art. 28. 1. Znakiem Rzeczypospolitej Polskiej jest wizerunek orła białego.\n\n"
    "Art. 29. Stolicą Rzeczypospolitej Polskiej jest Warszawa.\n\n"
    "Art. 30. Przyrodzona i niezbywalna godność człowieka stanowi źródło wolności."
)
ART_29 = "Art. 29. Stolicą Rzeczypospolitej Polskiej jest Warszawa."
CORPUS = files("meritum_core.corpus") / "migrations"
ROLLBACK = files("meritum_core.corpus.ready") / "rollback" / "0001_corpus_ready.sql"


def vector(text: str) -> str:
    embeddings = build_embeddings(EmbeddingsSettings(provider="stub"))
    found = asyncio.run(embeddings.embed_query(text))
    return "[" + ",".join(map(str, found)) + "]"


@pytest.fixture
def url() -> Iterator[str]:
    found = os.environ.get("MERITUM_CORPUS_DATABASE_URL", "")
    if not found:
        pytest.skip("set MERITUM_CORPUS_DATABASE_URL to the meritum-postgres image")
    with psycopg.connect(found, autocommit=True) as conn:
        conn.execute("CREATE SCHEMA IF NOT EXISTS corpus")
        conn.execute("CREATE SCHEMA IF NOT EXISTS corpus_ready")
        for name in ("0001_corpus_search.sql", "0003_corpus_documents.sql"):
            conn.execute((CORPUS / name).read_bytes())
    apply_corpus_ready_migrations(found)
    yield found
    with psycopg.connect(found, autocommit=True) as conn:
        conn.execute(ROLLBACK.read_bytes())
        conn.execute("DELETE FROM corpus.snapshot_manifest WHERE version = 'cr-v1'")
        conn.execute("DELETE FROM corpus.snapshots WHERE version = 'cr-v1'")
        conn.execute("DELETE FROM corpus.passages WHERE source_id LIKE 'cr-%'")
        conn.execute("DELETE FROM corpus.documents WHERE source_id LIKE 'cr-%'")


def load(url: str) -> None:
    start = FULL_TEXT.index(ART_29)
    with psycopg.connect(url, autocommit=True) as conn:
        for sid, text in (("cr-k", FULL_TEXT), ("cr-news", "Warszawa w liczbach")):
            conn.execute(
                "INSERT INTO corpus.documents (source_id, url, domain, publisher_id,"
                " license, fetched_at, checksum, full_text) VALUES"
                " (%s, %s, 'x', 'p', 'l', %s, 'c1', %s)",
                (sid, f"https://x/{sid}", TAKEN_AT, text),
            )
            conn.execute(
                "INSERT INTO corpus.passages (passage_id, source_id, text,"
                " fetched_at, added_at, embedding) VALUES (%s, %s, %s, %s, %s, %s)",
                (f"{sid}-p", sid, text, TAKEN_AT, TAKEN_AT, vector(text)),
            )
        conn.execute("INSERT INTO corpus.snapshots VALUES ('cr-v1', %s)", (TAKEN_AT,))
        conn.execute(
            "INSERT INTO corpus.snapshot_manifest SELECT 'cr-v1', source_id,"
            " checksum, fetched_at FROM corpus.documents WHERE source_id LIKE 'cr-%'"
        )
        conn.execute(
            "INSERT INTO corpus_ready.gold_chunks (chunk_id, source_id, checksum,"
            " start_offset, end_offset, text, header, kind, weight, embedding,"
            " build_id) VALUES ('cr-k:29', 'cr-k', 'c1', %s, %s, %s,"
            " 'Konstytucja RP (Dz.U. 1997 nr 78 poz. 483)', 'act', 1, %s, 'b1')",
            (start, start + len(ART_29), ART_29, vector(ART_29)),
        )


@pytest.mark.integration
def test_gold_chunk_replaces_bronze_of_its_document(
    url: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    load(url)
    monkeypatch.setenv("MERITUM_CORPUS_READY", "true")
    port = build_corpus_search(
        CorpusSettings(provider="postgres", database_url=url),
        build_embeddings(EmbeddingsSettings(provider="stub")),
    )

    found = asyncio.run(
        port.search(
            "stolica Warszawa", claim_date=date(2026, 11, 20), corpus_version="cr-v1"
        )
    )

    assert [p.passage_id for p in found] == ["gold:cr-k:29", "cr-news-p"]
    with psycopg.connect(url) as conn:
        row = conn.execute(
            "SELECT substr(d.full_text, g.start_offset + 1, g.end_offset - g.start_offset)"
            " FROM corpus_ready.gold_chunks g JOIN corpus.documents d USING (source_id)"
        ).fetchone()
    assert row == (ART_29,)


@pytest.mark.integration
def test_migrations_run_twice_and_roll_back(url: str) -> None:
    assert apply_corpus_ready_migrations(url) == []
