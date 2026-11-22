"""Builds the page fetcher; nothing else instantiates its adapters.

Features:
    US-SPR-07, US-KOR-03, F-06, ADR-32
"""

import httpx

from meritum_core.corpus.fetching.adapters import (
    Crawl4AiPageFetcher,
    HttpxPageFetcher,
    system_resolver,
)
from meritum_core.corpus.fetching.ports import PageFetcherPort, Resolver
from meritum_core.corpus.fetching.settings import FetchingSettings


def build_page_fetcher(
    *,
    settings: FetchingSettings | None = None,
    resolver: Resolver = system_resolver,
    transport: httpx.AsyncBaseTransport | None = None,
) -> PageFetcherPort:
    """Build the SSRF-safe fetcher on httpx, with Crawl4AI when it is configured.

    Args:
        settings: ``MERITUM_FETCH_*``; without ``crawl4ai_url`` pages that need
            JavaScript fail with ``javascript_required``.
        resolver: DNS lookup; the system resolver unless a test substitutes one.
        transport: httpx transport; only tests pass one (an in-process server).

    Returns:
        The page fetcher.

    Features:
        US-SPR-07, US-KOR-03, F-06, ADR-32
    """
    fetcher = HttpxPageFetcher(resolver=resolver, transport=transport)
    if settings is None or settings.crawl4ai_url is None:
        return fetcher
    token = settings.crawl4ai_token
    return Crawl4AiPageFetcher(
        fetcher,
        endpoint=str(settings.crawl4ai_url),
        token=token.get_secret_value() if token is not None else "",
        resolver=resolver,
        transport=transport,
    )
