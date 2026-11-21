"""Reranking of search passages before stance assessment (ADR-35).

Public API: the port, its result model, the null gate and the limit. The fake
for tests is in ``meritum_core.corpus.rerank.fakes``, the port contract every
adapter passes in ``meritum_core.corpus.rerank.contract``.

Features:
    US-KOR-02, US-SPR-04, F-12, ADR-35
"""

from meritum_core.corpus.rerank.constants import RERANK_TOP_K
from meritum_core.corpus.rerank.gates import NullReranker
from meritum_core.corpus.rerank.models import RankedPassage
from meritum_core.corpus.rerank.ports import RerankerPort

__all__ = ["RERANK_TOP_K", "NullReranker", "RankedPassage", "RerankerPort"]
