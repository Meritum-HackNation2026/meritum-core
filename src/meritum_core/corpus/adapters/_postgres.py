"""PostgreSQL corpus search: pgvector, Polish full text and pg_trgm, fused in Python.

Features:
    US-KOR-02, US-ZRD-05, F-12, ADR-04, ADR-19, ADR-32
"""

from dataclasses import dataclass, replace
from datetime import date, datetime
from typing import Final, LiteralString

from psycopg import AsyncConnection, Error
from psycopg.rows import class_row

from meritum_core.corpus.constants import (
    CANDIDATES_PER_RANKING,
    DEFAULT_LIMIT,
    TRIGRAM_THRESHOLD,
)
from meritum_core.corpus.errors import (
    CorpusUnavailableError,
    UnknownCorpusVersionError,
)
from meritum_core.corpus.fusion import fuse_rankings
from meritum_core.corpus.models import Passage
from meritum_core.shared.embeddings import EmbeddingsPort

_RANKINGS: Final[tuple[LiteralString, ...]] = (
    # Meaning: cosine distance on the HNSW index.
    """
    SELECT passage_id, source_id, text, published_on, fetched_at
    FROM corpus.passages
    WHERE added_at <= %(taken_at)s
      AND (retired_at IS NULL OR retired_at > %(taken_at)s)
    ORDER BY embedding <=> %(embedding)s::vector
    LIMIT %(candidates)s
    """,
    # Exact words, Polish dictionary; any query word may match (OR of lexemes).
    """
    WITH q AS (
        SELECT to_tsquery(
            'simple', coalesce(string_agg(quote_literal(lexeme), ' | '), '')
        ) AS ts
        FROM unnest(
            tsvector_to_array(to_tsvector('public.polish'::regconfig, %(query)s))
        ) AS lexeme
    )
    SELECT passage_id, source_id, text, published_on, fetched_at
    FROM corpus.passages, q
    WHERE added_at <= %(taken_at)s
      AND (retired_at IS NULL OR retired_at > %(taken_at)s)
      AND search_vector @@ q.ts
    ORDER BY ts_rank_cd(search_vector, q.ts) DESC
    LIMIT %(candidates)s
    """,
    # Typos: trigram word similarity.
    """
    SELECT passage_id, source_id, text, published_on, fetched_at
    FROM corpus.passages
    WHERE added_at <= %(taken_at)s
      AND (retired_at IS NULL OR retired_at > %(taken_at)s)
      AND %(query)s <%% text
    ORDER BY word_similarity(%(query)s, text) DESC
    LIMIT %(candidates)s
    """,
)
"""One query per ranking, each best first; ``fuse_rankings`` merges them.
A snapshot sees the passages added by and not retired at its ``taken_at`` (ADR-19)."""


@dataclass(frozen=True)
class _Params:
    query: str
    embedding: str
    candidates: int
    taken_at: datetime | None = None

    def bind(self) -> dict[str, str | int | datetime | None]:
        return {
            "query": self.query,
            "embedding": self.embedding,
            "candidates": self.candidates,
            "taken_at": self.taken_at,
        }


class PostgresCorpusSearch:
    """CorpusSearchPort over the shared ``corpus`` schema (ADR-32).

    Args:
        conninfo: libpq connection string.
        embeddings: Embeds the query with the model the corpus was indexed with.

    Features:
        US-KOR-02, US-ZRD-05, F-12, ADR-04, ADR-19, ADR-32
    """

    def __init__(self, conninfo: str, embeddings: EmbeddingsPort) -> None:
        self._conninfo = conninfo
        self._embeddings = embeddings

    async def search(
        self,
        query: str,
        *,
        claim_date: date,
        corpus_version: str,
        limit: int = DEFAULT_LIMIT,
    ) -> list[Passage]:
        """Search one snapshot (see ``CorpusSearchPort.search``).

        Args:
            query: The query text.
            claim_date: The date the claim is about.
            corpus_version: The pinned snapshot.
            limit: Most passages to return.

        Returns:
            Matching passages, best first.

        Raises:
            UnknownCorpusVersionError: No snapshot has this version.
            CorpusUnavailableError: PostgreSQL failed (connection or query).
        """
        vector = await self._embeddings.embed_query(query)
        params = _Params(
            query=query,
            embedding="[" + ",".join(map(str, vector)) + "]",
            candidates=CANDIDATES_PER_RANKING,
        )
        try:
            rankings = await self._rankings(corpus_version, params)
        except Error as exc:
            msg = "corpus search failed in PostgreSQL"
            raise CorpusUnavailableError(msg) from exc
        if rankings is None:
            raise UnknownCorpusVersionError(corpus_version)
        return fuse_rankings(rankings, claim_date=claim_date, limit=limit)

    async def _rankings(
        self, corpus_version: str, params: _Params
    ) -> list[list[Passage]] | None:
        # shortcut: one connection per search; take a pool from the caller when
        # search latency matters (ADR-20 budget).
        async with (
            await AsyncConnection.connect(self._conninfo) as conn,
            conn.transaction(),
        ):
            taken_at = await _snapshot_time(conn, corpus_version)
            if taken_at is None:
                return None
            await _set_search_options(conn)
            snapshot = replace(params, taken_at=taken_at)
            return [await _ranking(conn, sql, snapshot) for sql in _RANKINGS]


async def _snapshot_time(conn: AsyncConnection, corpus_version: str) -> datetime | None:
    cursor = await conn.execute(
        "SELECT taken_at FROM corpus.snapshots WHERE version = %s", (corpus_version,)
    )
    match await cursor.fetchone():
        case (datetime() as taken_at,):
            return taken_at
        case _:
            return None


async def _set_search_options(conn: AsyncConnection) -> None:
    # Iterative HNSW scan: the snapshot filter runs after the index scan (pgvector 0.8).
    await conn.execute("SET LOCAL hnsw.iterative_scan = strict_order")
    await conn.execute(
        "SELECT set_config('pg_trgm.word_similarity_threshold', %s, true)",
        (str(TRIGRAM_THRESHOLD),),
    )


async def _ranking(
    conn: AsyncConnection, sql: LiteralString, params: _Params
) -> list[Passage]:
    async with conn.cursor(row_factory=class_row(Passage)) as cursor:
        await cursor.execute(sql, params.bind())
        return await cursor.fetchall()
