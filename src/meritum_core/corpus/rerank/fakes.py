"""A configurable reranker for tests of the gate and of worker workflows.

Features:
    US-KOR-02, US-SPR-04, F-12, ADR-35
"""

from collections.abc import Mapping

from meritum_core.corpus.models import Passage
from meritum_core.corpus.rerank.constants import RERANK_TOP_K
from meritum_core.corpus.rerank.models import RankedPassage


class FakeReranker:
    """Scores passages from a preset map and records the claims it reranked.

    Attributes:
        claims: Claims passed to ``rerank``, in order.

    Args:
        relevance: Relevance per passage id; passages not in it score 0.

    Features:
        US-KOR-02, US-SPR-04, F-12, ADR-35
    """

    claims: list[str]

    def __init__(self, relevance: Mapping[str, float] | None = None) -> None:
        self._relevance = dict(relevance or {})
        self.claims = []

    async def rerank(
        self, claim: str, passages: list[Passage], *, limit: int = RERANK_TOP_K
    ) -> list[RankedPassage]:
        """Record ``claim`` and order ``passages`` by the preset relevance.

        Args:
            claim: The claim.
            passages: Passages from the search, best first.
            limit: Most passages to return.

        Returns:
            The ``limit`` most relevant passages; ties keep the search order.

        Raises:
            ValueError: ``limit`` is below 1.
        """
        if limit < 1:
            msg = f"limit must be at least 1, got {limit}"
            raise ValueError(msg)
        self.claims.append(claim)
        ranked = [
            RankedPassage(passage=p, relevance=self._relevance.get(p.passage_id, 0.0))
            for p in passages
        ]
        ranked.sort(key=lambda r: r.relevance, reverse=True)
        return ranked[:limit]
