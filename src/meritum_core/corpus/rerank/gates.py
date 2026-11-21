"""The null reranker: used until a provider is picked (worker/030, worker/031).

Features:
    US-KOR-02, US-SPR-04, F-12, ADR-35
"""

import logging

from meritum_core.corpus.models import Passage
from meritum_core.corpus.rerank.constants import RERANK_TOP_K
from meritum_core.corpus.rerank.models import RankedPassage

_log = logging.getLogger(__name__)


class NullReranker:
    """Keeps the search order, cuts it to the limit and logs that reranking was skipped.

    The relevance of each passage is its fused search score. The log line never
    holds the claim or passage text.

    Features:
        US-KOR-02, US-SPR-04, F-12, ADR-35
    """

    async def rerank(  # ruff: ignore[no-self-use]  # null object: same signature as a real reranker
        self,
        claim: str,  # ruff: ignore[unused-method-argument]  # null object ignores the claim
        passages: list[Passage],
        *,
        limit: int = RERANK_TOP_K,
    ) -> list[RankedPassage]:
        """Skip reranking.

        Args:
            claim: Ignored.
            passages: Passages from the search, best first.
            limit: Most passages to return.

        Returns:
            The first ``limit`` passages in search order.

        Raises:
            ValueError: ``limit`` is below 1.
        """
        if limit < 1:
            msg = f"limit must be at least 1, got {limit}"
            raise ValueError(msg)
        _log.info("reranker not configured; skipped for %d passages", len(passages))
        return [RankedPassage(passage=p, relevance=p.score) for p in passages[:limit]]
