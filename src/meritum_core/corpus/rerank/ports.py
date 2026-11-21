"""The reranker port: the cheap gate between search and stance assessment (ADR-35).

Features:
    US-KOR-02, US-SPR-04, F-12, ADR-35
"""

from typing import Protocol, runtime_checkable

from meritum_core.corpus.models import Passage
from meritum_core.corpus.rerank.constants import RERANK_TOP_K
from meritum_core.corpus.rerank.models import RankedPassage


@runtime_checkable
class RerankerPort(Protocol):
    """Orders passages by relevance to one claim and keeps the best few.

    Provider adapters (Vertex AI ranking API, bge-reranker on Cloudflare Workers
    AI) and the factory reading ``MERITUM_RERANKER`` live in the worker
    (worker/031), the only process that reranks. Core keeps the port, the null
    gate, a fake and the contract every adapter passes:
    ``meritum_core.corpus.rerank.contract.reranker_contract_violations``.

    Features:
        US-KOR-02, US-SPR-04, F-12, ADR-04, ADR-20, ADR-35
    """

    async def rerank(
        self, claim: str, passages: list[Passage], *, limit: int = RERANK_TOP_K
    ) -> list[RankedPassage]:
        """Return at most ``limit`` of ``passages``, most relevant to ``claim`` first.

        Args:
            claim: The claim, already masked (data, never instructions).
            passages: Passages from the hybrid or live search, best first.
            limit: Most passages to return.

        Returns:
            Passages taken from ``passages``, each once, with non-increasing
            relevance; empty when ``passages`` is empty.

        Raises:
            ValueError: ``limit`` is below 1.
            ProviderUnavailableError: The provider failed after retries.
        """
        ...
