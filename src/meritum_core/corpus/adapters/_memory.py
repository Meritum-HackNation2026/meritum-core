"""In-memory corpus search: the fake for tests and runs without a database.

Features:
    US-KOR-02, US-ZRD-05, F-12, ADR-19
"""

import re
from collections.abc import Mapping, Sequence
from datetime import date

from meritum_core.corpus.constants import (
    CANDIDATES_PER_RANKING,
    DEFAULT_LIMIT,
    MEMORY_STEM_LENGTH,
)
from meritum_core.corpus.errors import UnknownCorpusVersionError
from meritum_core.corpus.fusion import fuse_rankings
from meritum_core.corpus.models import Passage
from meritum_core.shared.embeddings import EmbeddingsPort, Vector


class MemoryCorpusSearch:
    """Vector and word-stem rankings over in-process snapshots, fused like PostgreSQL.

    Args:
        snapshots: Passages per ``corpus_version``.
        embeddings: Embeds queries and passages.

    Features:
        US-KOR-02, US-ZRD-05, F-12, ADR-19
    """

    def __init__(
        self, snapshots: Mapping[str, Sequence[Passage]], embeddings: EmbeddingsPort
    ) -> None:
        self._snapshots = dict(snapshots)
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
        """
        if corpus_version not in self._snapshots:
            raise UnknownCorpusVersionError(corpus_version)
        passages = self._snapshots[corpus_version]
        query_vector = await self._embeddings.embed_query(query)
        vectors = await self._embeddings.embed_documents([p.text for p in passages])
        semantic = [_dot(query_vector, v) for v in vectors]
        stems = _stems(query)
        lexical = [len(stems & _stems(p.text)) for p in passages]
        rankings = [_ranked(passages, semantic), _ranked(passages, lexical)]
        return fuse_rankings(rankings, claim_date=claim_date, limit=limit)


def _stems(text: str) -> set[str]:
    return {word[:MEMORY_STEM_LENGTH] for word in re.findall(r"\w+", text.lower())}


def _dot(a: Vector, b: Vector) -> float:
    return sum(x * y for x, y in zip(a, b, strict=True))


def _ranked(passages: Sequence[Passage], scores: Sequence[float]) -> list[Passage]:
    # Stable sort: equal scores keep the snapshot's order.
    order = sorted(range(len(passages)), key=lambda i: -scores[i])
    return [passages[i] for i in order if scores[i] > 0][:CANDIDATES_PER_RANKING]
