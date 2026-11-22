"""build_corpus_search with MERITUM_CORPUS_READY off and on, over a fake PostgreSQL.

The fake records every SQL statement, so the flag-off test proves the bronze
path never touches ``corpus_ready``.
"""

import asyncio
from collections.abc import Callable
from datetime import UTC, date, datetime
from typing import Self

import psycopg
import pytest
from pydantic import SecretStr

from meritum_core.corpus import (
    CorpusProvider,
    CorpusSearchPort,
    CorpusSettings,
    Passage,
    build_corpus_search,
)
from meritum_core.corpus.ready import DocumentKind, GoldHit
from meritum_core.shared.embeddings import EmbeddingsSettings, build_embeddings

FETCHED = datetime(2026, 11, 1, tzinfo=UTC)
CONSTITUTION = "src-konstytucja"
ART_29 = "Art. 29. Stolicą Rzeczypospolitej Polskiej jest Warszawa."
BRONZE = [
    Passage(
        passage_id="b1",
        source_id=CONSTITUTION,
        text="Art. 28. ... Art. 29. ...",
        published_on=None,
        fetched_at=FETCHED,
    ),
    Passage(
        passage_id="b2",
        source_id="src-news",
        text="Warszawa w liczbach",
        published_on=date(2026, 11, 10),
        fetched_at=FETCHED,
    ),
]
GOLD = GoldHit(
    chunk_id="k:29",
    source_id=CONSTITUTION,
    text=ART_29,
    published_on=date(1997, 7, 16),
    fetched_at=FETCHED,
    kind=DocumentKind.ACT,
    valid_from=date(1997, 10, 17),
    valid_to=None,
    weight=1.0,
)


class FakeCursor:
    """Answers each statement from ``answer`` and logs it."""

    def __init__(self, log: list[str], answer: Callable[[str], list[object]]) -> None:
        self.log, self.answer, self.rows = log, answer, list[object]()

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(self, *_: object) -> None:
        return None

    async def execute(self, sql: str | bytes, _params: object = None) -> Self:
        text = sql.decode() if isinstance(sql, bytes) else sql
        self.log.append(text)
        self.rows = self.answer(text)
        return self

    async def fetchone(self) -> object:
        return self.rows[0] if self.rows else None

    async def fetchall(self) -> list[object]:
        return self.rows


class FakeConnection(FakeCursor):
    """Enough of ``psycopg.AsyncConnection`` for both adapters."""

    def transaction(self) -> Self:
        return self

    def cursor(self, **_: object) -> FakeCursor:
        return FakeCursor(self.log, self.answer)


def answer(sql: str) -> list[object]:
    """Rows a populated database would return for each statement."""
    if "corpus.snapshots WHERE version" in sql:
        return [(FETCHED,)]
    if "corpus_ready" in sql:
        return [(CONSTITUTION,)] if "DISTINCT" in sql else [GOLD]
    if "corpus.passages" in sql:
        return list(BRONZE)
    return []


@pytest.fixture
def statements(monkeypatch: pytest.MonkeyPatch) -> list[str]:
    log: list[str] = []

    async def connect(*_: object, **__: object) -> FakeConnection:  # ruff: ignore[unused-async]  # replaces an async classmethod
        return FakeConnection(log, answer)

    monkeypatch.setattr(psycopg.AsyncConnection, "connect", connect)
    return log


def search(query: str) -> list[Passage]:
    settings = CorpusSettings(
        provider=CorpusProvider.POSTGRES, database_url=SecretStr("postgresql://fake")
    )
    port: CorpusSearchPort = build_corpus_search(
        settings, build_embeddings(EmbeddingsSettings())
    )
    return asyncio.run(
        port.search(query, claim_date=date(2026, 11, 20), corpus_version="v1")
    )


def test_flag_off_search_never_touches_corpus_ready(
    statements: list[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("MERITUM_CORPUS_READY", raising=False)

    found = search("Warszawa jest stolicą Polski")

    assert statements
    assert not [s for s in statements if "corpus_ready" in s]
    assert {p.passage_id for p in found} == {"b1", "b2"}


def test_flag_false_is_off(
    statements: list[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("MERITUM_CORPUS_READY", "false")

    search("Warszawa")

    assert not [s for s in statements if "corpus_ready" in s]


def test_flag_on_gold_replaces_bronze_of_covered_document(
    statements: list[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("MERITUM_CORPUS_READY", "true")

    found = search("Warszawa jest stolicą Polski")

    assert [s for s in statements if "corpus_ready" in s]
    assert found[0].passage_id == "gold:k:29"
    assert found[0].text == ART_29
    assert [p.passage_id for p in found[1:]] == ["b2"]


def test_flag_on_gold_failure_keeps_bronze(
    statements: list[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("MERITUM_CORPUS_READY", "true")

    def broken(sql: str) -> list[object]:
        if "corpus_ready" in sql:
            raise psycopg.errors.UndefinedTable(sql)
        return answer(sql)

    async def connect(*_: object, **__: object) -> FakeConnection:  # ruff: ignore[unused-async]  # replaces an async classmethod
        return FakeConnection(statements, broken)

    monkeypatch.setattr(psycopg.AsyncConnection, "connect", connect)

    assert {p.passage_id for p in search("Warszawa")} == {"b1", "b2"}
