"""Gold-first corpus search: bronze search as today, gold chunks merged in.

Features:
    US-KOR-02, US-ZRD-05, F-12, ADR-19, ADR-32
"""

import logging
from datetime import date
from itertools import starmap
from typing import Final, LiteralString

from psycopg import AsyncConnection, Error
from psycopg.rows import class_row

from meritum_core.corpus.constants import CANDIDATES_PER_RANKING, DEFAULT_LIMIT
from meritum_core.corpus.models import Passage
from meritum_core.corpus.ports import CorpusSearchPort
from meritum_core.corpus.ready.merge import fuse_gold, merge_with_bronze
from meritum_core.corpus.ready.models import GoldHit
from meritum_core.shared.embeddings import EmbeddingsPort, Vector

_log = logging.getLogger(__name__)

_VISIBLE: Final[LiteralString] = """
    FROM corpus_ready.gold_chunks g
    JOIN corpus.snapshots s ON s.version = %(version)s
    JOIN corpus.snapshot_manifest m
      ON m.version = s.version AND m.source_id = g.source_id
     AND m.checksum = g.checksum
    JOIN corpus.documents d ON d.source_id = g.source_id
     AND (d.retired_at IS NULL OR d.retired_at > s.taken_at)
"""
"""Gold chunks a snapshot may see: document version (checksum) in its manifest,
document not retired or removed at its time (ADR-19)."""
_COLUMNS: Final[LiteralString] = """
    SELECT g.chunk_id, g.source_id, g.text, g.published_on, m.fetched_at,
           g.kind, g.valid_from, g.valid_to, g.weight
"""
"""The ``GoldHit`` columns of a gold ranking."""
_QUERY_TERMS: Final[LiteralString] = """
    WITH q AS (
        SELECT to_tsquery(
            'simple', coalesce(string_agg(quote_literal(lexeme), ' | '), '')
        ) AS ts
        FROM unnest(
            tsvector_to_array(to_tsvector('public.polish'::regconfig, %(query)s))
        ) AS lexeme
    )
"""
"""Query lexemes OR-ed, as in the bronze full-text ranking."""
_BY_MEANING: Final[LiteralString] = (
    "ORDER BY g.embedding <=> %(embedding)s::vector LIMIT %(candidates)s"
)
"""Order of the vector ranking: cosine distance on the HNSW index."""
_BY_WORDS: Final[LiteralString] = """
    , q WHERE g.search_vector @@ q.ts
    ORDER BY ts_rank_cd(g.search_vector, q.ts) DESC
    LIMIT %(candidates)s
"""
"""Filter and order of the full-text ranking."""
_RANKINGS: Final[tuple[LiteralString, ...]] = (
    _COLUMNS + _VISIBLE + _BY_MEANING,
    _QUERY_TERMS + _COLUMNS + _VISIBLE + _BY_WORDS,
)
"""Vector and full-text rankings of gold (header and text both indexed)."""

_COVERED: Final[LiteralString] = (
    "SELECT DISTINCT g.source_id" + _VISIBLE + "WHERE g.source_id = ANY(%(ids)s)"
)
"""Which of the bronze result's documents have gold chunks in the snapshot."""


class PostgresGoldSearch:
    """CorpusSearchPort that adds gold chunks to an unchanged bronze search.

    Bronze runs first and exactly as without the layer. Gold replaces the bronze
    passages of the documents it covers; any gold failure returns bronze as is.

    Args:
        bronze: Today's search (``PostgresCorpusSearch``).
        conninfo: libpq connection string of the database with both schemas.
        embeddings: Embeds the query with the model gold was indexed with.

    Features:
        US-KOR-02, US-ZRD-05, F-12, ADR-19, ADR-32
    """

    def __init__(
        self, bronze: CorpusSearchPort, conninfo: str, embeddings: EmbeddingsPort
    ) -> None:
        self._bronze = bronze
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
        """Search bronze, then merge gold (see ``CorpusSearchPort.search``).

        Args:
            query: The query text.
            claim_date: The date the claim is about.
            corpus_version: The pinned snapshot.
            limit: Most passages to return.

        Returns:
            Passages best first; gold ones have ``passage_id`` ``gold:<chunk_id>``.
        """
        bronze = await self._bronze.search(
            query, claim_date=claim_date, corpus_version=corpus_version, limit=limit
        )
        try:
            # shortcut: the query is embedded a second time; share the vector
            # with bronze if the embeddings bill or latency matters.
            vector = await self._embeddings.embed_query(query)
            rankings, covered = await self._gold(query, vector, corpus_version, bronze)
        except Error:
            _log.warning(
                "corpus_ready search failed; bronze result kept", exc_info=True
            )
            return bronze
        gold = fuse_gold(rankings, claim_date=claim_date)
        return merge_with_bronze(gold, bronze, covered=covered, limit=limit)

    async def _gold(
        self,
        query: str,
        vector: Vector,
        version: str,
        bronze: list[Passage],
    ) -> tuple[list[list[GoldHit]], set[str]]:
        params = {
            "query": query,
            "embedding": "[" + ",".join(map(str, vector)) + "]",
            "candidates": CANDIDATES_PER_RANKING,
            "version": version,
            "ids": sorted({p.source_id for p in bronze}),
        }
        async with await AsyncConnection.connect(self._conninfo) as conn:
            await conn.execute("SET hnsw.iterative_scan = strict_order")
            rankings = []
            for sql in _RANKINGS:
                async with conn.cursor(row_factory=class_row(GoldHit)) as cursor:
                    await cursor.execute(sql, params)
                    rankings.append(await cursor.fetchall())
            cursor = await conn.execute(_COVERED, params)
            covered = set(starmap(str, await cursor.fetchall()))
        return rankings, covered
