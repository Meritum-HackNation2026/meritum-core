"""scripts/reembed_corpus.py: refuses non-EU runs; re-embeds passages in place.

The integration test needs the meritum-postgres image and
``MERITUM_CORPUS_DATABASE_URL`` (``uv run pytest -m integration tests/corpus``).
"""

import asyncio
import os
import runpy
import uuid
from pathlib import Path

import psycopg
import pytest

from meritum_core.shared.embeddings import EmbeddingsSettings, build_embeddings

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = runpy.run_path(str(ROOT / "scripts" / "reembed_corpus.py"))
ZERO = "[" + ",".join(["0"] * 768) + "]"


def test_stub_embeddings_are_refused(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MERITUM_EMBEDDINGS_PROVIDER", "stub")
    monkeypatch.setenv("MERITUM_CORPUS_DATABASE_URL", "postgresql://x@127.0.0.1:1/x")
    assert SCRIPT["main"]() == SCRIPT["USAGE_ERROR"]


def test_missing_database_is_refused(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MERITUM_EMBEDDINGS_PROVIDER", "vertex")
    monkeypatch.delenv("MERITUM_CORPUS_DATABASE_URL", raising=False)
    assert SCRIPT["main"]() == SCRIPT["USAGE_ERROR"]


@pytest.mark.integration
def test_every_passage_gets_a_new_vector() -> None:
    url = os.environ.get("MERITUM_CORPUS_DATABASE_URL", "")
    if not url:
        pytest.skip("set MERITUM_CORPUS_DATABASE_URL to the meritum-postgres image")
    migration = ROOT / "src/meritum_core/corpus/migrations/0001_corpus_search.sql"
    prefix = uuid.uuid4().hex
    texts = [f"Komunikat numer {i} o burzach" for i in range(11)]
    with psycopg.connect(url, autocommit=True) as conn:
        conn.execute(migration.read_bytes())
        for i, text in enumerate(texts):
            conn.execute(
                "INSERT INTO corpus.passages (passage_id, source_id, text,"
                " fetched_at, embedding) VALUES (%s, 'src', %s, now(), %s::vector)",
                (f"{prefix}-{i:02}", text, ZERO),
            )
    stub = build_embeddings(EmbeddingsSettings(provider="stub"))
    try:
        count = asyncio.run(SCRIPT["reembed"](url, stub, batch=4))
        with psycopg.connect(url) as conn:
            zeros = conn.execute(
                "SELECT count(*) FROM corpus.passages"
                " WHERE passage_id LIKE %s AND embedding = %s::vector",
                (f"{prefix}%", ZERO),
            ).fetchone()
    finally:
        with psycopg.connect(url, autocommit=True) as conn:
            conn.execute(
                "DELETE FROM corpus.passages WHERE passage_id LIKE %s", (f"{prefix}%",)
            )
    assert count >= len(texts)
    assert zeros == (0,)
