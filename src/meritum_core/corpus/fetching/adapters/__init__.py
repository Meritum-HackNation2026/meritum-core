"""Adapters of the page fetcher port.

Features:
    US-SPR-07, F-06
"""

from meritum_core.corpus.fetching.adapters._crawl4ai import Crawl4AiPageFetcher
from meritum_core.corpus.fetching.adapters._guard import system_resolver
from meritum_core.corpus.fetching.adapters._httpx import HttpxPageFetcher

__all__ = ["Crawl4AiPageFetcher", "HttpxPageFetcher", "system_resolver"]
