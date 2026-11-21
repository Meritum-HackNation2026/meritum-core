"""CorpusSearchPort on the in-memory adapter: pinned snapshots, Polish inflection."""

import asyncio
from datetime import UTC, date, datetime

import pytest

from meritum_core.corpus import (
    CorpusSearchPort,
    CorpusSettings,
    Passage,
    UnknownCorpusVersionError,
    build_corpus_search,
)
from meritum_core.shared.embeddings import EmbeddingsSettings, build_embeddings

CLAIM_DATE = date(2026, 11, 20)


def passage(passage_id: str, text: str) -> Passage:
    return Passage(
        passage_id=passage_id,
        source_id=f"src-{passage_id}",
        text=text,
        published_on=date(2026, 11, 1),
        fetched_at=datetime(2026, 11, 2, tzinfo=UTC),
    )


def memory(snapshots: dict[str, list[Passage]]) -> CorpusSearchPort:
    embeddings = build_embeddings(EmbeddingsSettings(provider="stub"))
    return build_corpus_search(
        CorpusSettings(provider="memory"), embeddings, snapshots=snapshots
    )


def test_search_reads_only_the_pinned_snapshot() -> None:
    old = [passage("old", "Ostrzeżenie przed burzami")]
    new = [*old, passage("new", "Ostrzeżenie przed burzami i gradem")]
    search = memory({"v1": old, "v2": new})
    found = asyncio.run(
        search.search("burza", claim_date=CLAIM_DATE, corpus_version="v1")
    )
    assert [p.passage_id for p in found] == ["old"]


def test_unknown_snapshot_is_an_error_not_an_empty_answer() -> None:
    search = memory({"v1": []})
    with pytest.raises(UnknownCorpusVersionError):
        asyncio.run(search.search("burze", claim_date=CLAIM_DATE, corpus_version="v9"))


def test_results_carry_source_id_and_dates() -> None:
    search = memory({"v1": [passage("a", "Komunikat o burzach")]})
    (found,) = asyncio.run(
        search.search("burza", claim_date=CLAIM_DATE, corpus_version="v1")
    )
    assert (found.source_id, found.published_on) == ("src-a", date(2026, 11, 1))
    assert found.fetched_at.tzinfo is not None


def test_unrelated_passages_are_not_returned() -> None:
    search = memory({"v1": [passage("a", "Ceny paliw")]})
    found = asyncio.run(
        search.search("burza gradowa", claim_date=CLAIM_DATE, corpus_version="v1")
    )
    assert found == []


def test_postgres_provider_requires_a_database_url() -> None:
    with pytest.raises(ValueError, match="DATABASE_URL"):
        CorpusSettings(provider="postgres")
