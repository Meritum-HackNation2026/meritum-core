"""Provider adapters of live web search.

Features:
    US-KOR-04, US-WDR-02, F-13
"""

from meritum_core.corpus.web_search.adapters._stub import StubWebSearch
from meritum_core.corpus.web_search.adapters._vertex_search import VertexWebSearch

__all__ = ["StubWebSearch", "VertexWebSearch"]
