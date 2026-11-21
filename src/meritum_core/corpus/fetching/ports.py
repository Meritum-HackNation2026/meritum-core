"""Port of the page fetcher: the only way Meritum reads a URL (rule 10).

Features:
    US-SPR-07, F-06
"""

import ipaddress
from collections.abc import Awaitable, Callable
from typing import Protocol

from meritum_core.corpus.fetching.models import FetchedPage, FetchPurpose

type IpAddress = ipaddress.IPv4Address | ipaddress.IPv6Address
"""One resolved address."""

type Resolver = Callable[[str], Awaitable[list[IpAddress]]]
"""DNS lookup: a host name to every A and AAAA address (tests substitute one)."""


class PageFetcherPort(Protocol):
    """Fetches one public http(s) page and returns its main text.

    Features:
        US-SPR-07, F-06, ADR-12
    """

    async def fetch(self, url: str, *, purpose: FetchPurpose) -> FetchedPage:
        """Fetch ``url`` without reaching internal addresses.

        Args:
            url: an absolute http(s) URL from a citizen, the catalogue or a search.
            purpose: ``SOURCE`` also honours robots.txt and Content-Signal.

        Returns:
            The page's main text, marked as untrusted data.

        Raises:
            PageFetchError: The page could not be fetched; ``reason`` says why.
        """
        ...
