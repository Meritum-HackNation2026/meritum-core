"""Builds the page fetcher; nothing else instantiates its adapter.

Features:
    US-SPR-07, F-06
"""

import httpx

from meritum_core.corpus.fetching.adapters import HttpxPageFetcher, system_resolver
from meritum_core.corpus.fetching.ports import PageFetcherPort, Resolver


def build_page_fetcher(
    *,
    resolver: Resolver = system_resolver,
    transport: httpx.AsyncBaseTransport | None = None,
) -> PageFetcherPort:
    """Build the SSRF-safe fetcher on httpx.

    Args:
        resolver: DNS lookup; the system resolver unless a test substitutes one.
        transport: httpx transport; only tests pass one (an in-process server).

    Returns:
        The page fetcher.

    Features:
        US-SPR-07, F-06
    """
    return HttpxPageFetcher(resolver=resolver, transport=transport)
