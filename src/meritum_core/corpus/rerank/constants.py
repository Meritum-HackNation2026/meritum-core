"""Limits of the reranking gate before stance assessment.

Features:
    US-KOR-02, US-SPR-04, F-12, ADR-35
"""

from typing import Final

RERANK_TOP_K: Final = 5
"""Most passages per claim that reach stance assessment after reranking (ADR-35).
The hybrid search hands over up to 20; each kept passage costs one model call in
stance assessment, so fewer, better passages cut time and cost of a check. Tune
on the golden set together with the reranker choice (worker/030)."""
