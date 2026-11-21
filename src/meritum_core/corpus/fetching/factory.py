"""Builds the page fetcher; nothing else instantiates its adapter.

Features:
    US-SPR-07, F-06
"""

from meritum_core.corpus.fetching.adapters import HttpxPageFetcher
from meritum_core.corpus.fetching.ports import PageFetcherPort


def build_page_fetcher() -> PageFetcherPort:
    """Build the SSRF-safe fetcher on httpx with the system DNS resolver.

    Returns:
        The page fetcher.

    Features:
        US-SPR-07, F-06
    """
    return HttpxPageFetcher()
