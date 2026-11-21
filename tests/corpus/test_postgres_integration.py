"""PostgresCorpusSearch on a real database: local only, ``uv run pytest -m integration``.

Needs the meritum-postgres image from meritum-infra (pgvector, pg_trgm and the
``public.polish`` configuration) and ``MERITUM_CORPUS_DATABASE_URL``. The test
applies the migration and removes only the rows it added.
"""

import asyncio
import os
import uuid
from collections.abc import Iterator
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from importlib.resources import files

import psycopg
import pytest

from meritum_core.corpus import (
    CorpusSearchPort,
    CorpusSettings,
    CorpusUnavailableError,
    UnknownCorpusVersionError,
    build_corpus_search,
)
from meritum_core.shared.embeddings import EmbeddingsSettings, build_embeddings

CLAIM_DATE = date(2026, 11, 20)
WEEK_AGO = CLAIM_DATE - timedelta(days=7)
TAKEN_AT = datetime(2026, 11, 21, 12, tzinfo=UTC)
MIGRATION = files("meritum_core.corpus") / "migrations" / "0001_corpus_search.sql"
INSERT = """
INSERT INTO corpus.passages (passage_id, source_id, text, published_on,
    fetched_at, added_at, retired_at, embedding)
VALUES (%s, 'src', %s, %s, %s, %s, %s, %s::vector)
"""
DISTRACTORS = (
    "Sejm uchwalił ustawę o podatku od nieruchomości",
    "Ceny paliw na stacjach w listopadzie",
    "Szczepienia przeciw grypie w aptekach",
    "Rozkład jazdy pociągów regionalnych w województwie śląskim",
    "Wyniki matur z matematyki w 2026 roku",
    "Komunikat o jakości wody w Krakowie",
    "Nowe przepisy o ochronie danych osobowych",
    "Remont mostu na Wiśle potrwa do wiosny",
)


@dataclass(frozen=True)
class Row:
    """One passage to insert; times are relative to the snapshot's taken_at."""

    pid: str
    text: str
    published_on: date | None = WEEK_AGO
    added: timedelta = timedelta(hours=-1)
    retired: timedelta | None = None


@pytest.fixture
def url() -> str:
    found = os.environ.get("MERITUM_CORPUS_DATABASE_URL", "")
    if not found:
        pytest.skip("set MERITUM_CORPUS_DATABASE_URL to the meritum-postgres image")
    with psycopg.connect(found, autocommit=True) as conn:
        conn.execute("CREATE SCHEMA IF NOT EXISTS corpus")  # the platform's job
        conn.execute(MIGRATION.read_bytes())
    return found


@pytest.fixture
def corpus(url: str) -> Iterator[tuple[str, str]]:
    """A snapshot version for this test's own passages; returns (url, version)."""
    prefix = uuid.uuid4().hex
    yield url, prefix
    with psycopg.connect(url, autocommit=True) as conn:
        like = (f"{prefix}%",)
        conn.execute("DELETE FROM corpus.passages WHERE passage_id LIKE %s", like)
        conn.execute("DELETE FROM corpus.snapshots WHERE version LIKE %s", like)


def load(url: str, version: str, rows: list[Row]) -> None:
    embeddings = build_embeddings(EmbeddingsSettings(provider="stub"))
    vectors = asyncio.run(embeddings.embed_documents([r.text for r in rows]))
    with psycopg.connect(url, autocommit=True) as conn:
        for row, vector in zip(rows, vectors, strict=True):
            retired = None if row.retired is None else TAKEN_AT + row.retired
            literal = "[" + ",".join(map(str, vector)) + "]"
            values = (f"{version}-{row.pid}", row.text, row.published_on, TAKEN_AT)
            conn.execute(INSERT, (*values, TAKEN_AT + row.added, retired, literal))
        conn.execute(
            "INSERT INTO corpus.snapshots VALUES (%s, %s)", (version, TAKEN_AT)
        )


def search(url: str, query: str, version: str) -> list[str]:
    port: CorpusSearchPort = build_corpus_search(
        CorpusSettings(provider="postgres", database_url=url),
        build_embeddings(EmbeddingsSettings(provider="stub")),
    )
    found = asyncio.run(
        port.search(query, claim_date=CLAIM_DATE, corpus_version=version)
    )
    return [p.passage_id.removeprefix(f"{version}-") for p in found]


def distractors() -> list[Row]:
    return [Row(f"d{i}", text) for i, text in enumerate(DISTRACTORS)]


@pytest.mark.integration
def test_issue_scenario_inflected_query_finds_the_passage(
    corpus: tuple[str, str],
) -> None:
    url, version = corpus
    target = Row("target", "Ostrzeżenia meteorologiczne dla województwa mazowieckiego")
    load(url, version, [*distractors(), target])
    assert "target" in search(url, "ostrzeżenie meteorologiczne Mazowsze", version)[:5]


@pytest.mark.integration
def test_polish_dictionary_matches_a_form_no_other_ranking_can(
    corpus: tuple[str, str],
) -> None:
    # "psa" -> "pies" only through hunspell-pl: trigram similarity is 0.25 (below
    # TRIGRAM_THRESHOLD) and the stub embeddings share no stem.
    url, version = corpus
    load(
        url, version, [*distractors(), Row("target", "Pies sąsiada szczekał całą noc")]
    )
    assert search(url, "psa", version)[0] == "target"


@pytest.mark.integration
def test_snapshot_sees_only_rows_live_at_its_taken_at(corpus: tuple[str, str]) -> None:
    url, version = corpus
    text = "Ostrzeżenie przed burzami z gradem"
    rows = [
        Row("live", text),
        Row("added-later", text, added=timedelta(hours=1)),
        Row("retired-before", text, retired=timedelta(minutes=-5)),
        Row("retired-later", text, retired=timedelta(hours=1)),
    ]
    load(url, version, rows)
    assert sorted(search(url, "burza z gradem", version)) == ["live", "retired-later"]


@pytest.mark.integration
def test_fresher_passage_beats_a_slightly_better_older_match(
    corpus: tuple[str, str],
) -> None:
    url, version = corpus
    text = "Komunikat IMGW o przymrozkach w województwie mazowieckim"
    aged = Row("aged", f"{text}, przymrozki", CLAIM_DATE - timedelta(days=400))
    fresh = Row("fresh", text, CLAIM_DATE - timedelta(days=3))
    load(url, version, [aged, fresh])
    found = search(url, "przymrozki na Mazowszu", version)
    assert found.index("fresh") < found.index("aged")


@pytest.mark.integration
def test_unknown_snapshot_is_an_error(url: str) -> None:
    with pytest.raises(UnknownCorpusVersionError):
        search(url, "burza", f"{uuid.uuid4().hex}-missing")


@pytest.mark.integration
def test_unreachable_database_is_corpus_unavailable() -> None:
    url = "postgresql://x@127.0.0.1:1/x"
    with pytest.raises(CorpusUnavailableError):
        search(url, "burza", "v")
