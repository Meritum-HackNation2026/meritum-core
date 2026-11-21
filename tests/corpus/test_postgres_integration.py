"""PostgresCorpusSearch on a real database: local only, ``uv run pytest -m integration``.

Needs the meritum-postgres image from meritum-infra (pgvector, pg_trgm and the
``public.polish`` configuration) and ``MERITUM_CORPUS_DATABASE_URL``. The test
applies the migration and removes only the rows it added.
"""

import asyncio
import os
import uuid
from collections.abc import Iterator
from datetime import UTC, date, datetime, timedelta
from importlib.resources import files

import psycopg
import pytest

from meritum_core.corpus import (
    CorpusSearchPort,
    CorpusSettings,
    UnknownCorpusVersionError,
    build_corpus_search,
)
from meritum_core.shared.embeddings import EmbeddingsSettings, build_embeddings

CLAIM_DATE = date(2026, 11, 20)
MIGRATION = files("meritum_core.corpus") / "migrations" / "0001_corpus_search.sql"
INSERT = """
INSERT INTO corpus.passages
    (passage_id, source_id, text, published_on, fetched_at, added_at, embedding)
VALUES (%s, %s, %s, %s, %s, %s, %s::vector)
"""
DISTRACTORS = (
    "Sejm uchwalił ustawę o podatku od nieruchomości",
    "Ceny paliw na stacjach w listopadzie",
    "Szczepienia przeciw grypie w aptekach",
)

type Rows = list[tuple[str, str, date]]


@pytest.fixture
def url() -> str:
    found = os.environ.get("MERITUM_CORPUS_DATABASE_URL", "")
    if not found:
        pytest.skip("set MERITUM_CORPUS_DATABASE_URL to the meritum-postgres image")
    with psycopg.connect(found, autocommit=True) as conn:
        conn.execute(MIGRATION.read_bytes())
    return found


@pytest.fixture
def corpus(url: str) -> Iterator[tuple[str, str]]:
    """A snapshot version for this test's own passages; returns (url, version)."""
    prefix = uuid.uuid4().hex
    yield url, f"{prefix}-v1"
    with psycopg.connect(url, autocommit=True) as conn:
        conn.execute(
            "DELETE FROM corpus.passages WHERE passage_id LIKE %s", (f"{prefix}%",)
        )
        conn.execute(
            "DELETE FROM corpus.snapshots WHERE version LIKE %s", (f"{prefix}%",)
        )


def load(url: str, version: str, passages: Rows) -> None:
    embeddings = build_embeddings(EmbeddingsSettings(provider="stub"))
    vectors = asyncio.run(embeddings.embed_documents([text for _, text, _ in passages]))
    taken_at = datetime(2026, 11, 21, 12, tzinfo=UTC)
    prefix = version.removesuffix("-v1")
    with psycopg.connect(url, autocommit=True) as conn:
        literals = ["[" + ",".join(map(str, v)) + "]" for v in vectors]
        for (pid, text, published), literal in zip(passages, literals, strict=True):
            row = (
                f"{prefix}-{pid}",
                "src",
                text,
                published,
                taken_at,
                taken_at,
                literal,
            )
            conn.execute(INSERT, row)
        conn.execute(
            "INSERT INTO corpus.snapshots VALUES (%s, %s)", (version, taken_at)
        )
        late = taken_at + timedelta(hours=1)
        conn.execute(
            INSERT,
            (f"{prefix}-late", "src", passages[0][1], None, late, late, literals[0]),
        )


def search(url: str, query: str, version: str) -> list[str]:
    port: CorpusSearchPort = build_corpus_search(
        CorpusSettings(provider="postgres", database_url=url),
        build_embeddings(EmbeddingsSettings(provider="stub")),
    )
    found = asyncio.run(
        port.search(query, claim_date=CLAIM_DATE, corpus_version=version)
    )
    return [p.passage_id.split("-", 1)[1] for p in found]


@pytest.mark.integration
def test_polish_inflection_finds_the_passage(corpus: tuple[str, str]) -> None:
    url, version = corpus
    week_ago = CLAIM_DATE - timedelta(days=7)
    passages = [(f"d{i}", t, week_ago) for i, t in enumerate(DISTRACTORS)]
    target = "Ostrzeżenia meteorologiczne dla województwa mazowieckiego"
    load(url, version, [*passages, ("target", target, week_ago)])
    found = search(url, "ostrzeżenie meteorologiczne Mazowsze", version)
    assert "target" in found[:5]
    assert "late" not in found  # added after the snapshot


@pytest.mark.integration
def test_fresher_passage_ranks_higher(corpus: tuple[str, str]) -> None:
    url, version = corpus
    text = "Komunikat IMGW o przymrozkach w województwie mazowieckim"
    load(
        url,
        version,
        [
            ("stale", text, CLAIM_DATE - timedelta(days=400)),
            ("fresh", text, CLAIM_DATE - timedelta(days=3)),
        ],
    )
    found = search(url, "przymrozki na Mazowszu", version)
    assert found.index("fresh") < found.index("stale")


@pytest.mark.integration
def test_unknown_snapshot_is_an_error(url: str) -> None:
    with pytest.raises(UnknownCorpusVersionError):
        search(url, "burza", f"{uuid.uuid4().hex}-missing")
