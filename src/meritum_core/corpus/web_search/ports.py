"""Ports of live web search: the one callers use and the one providers implement.

Callers (research agents) use ``WebSearchPort``. A provider adapter (Vertex AI
Search here, SearXNG or Linkup in core/024) implements ``WebSearchProviderPort``;
``build_web_search`` wraps it with the catalogue filter, the time limit and the
query limit, so every provider answers through the same ``WebSearchPort``.

Features:
    US-KOR-04, US-WDR-02, F-13, ADR-07
"""

from typing import Protocol

from meritum_core.corpus.web_search.constants import DEFAULT_RESULTS
from meritum_core.corpus.web_search.models import WebSearchCandidate
from meritum_core.security import MaskedText


class WebSearchPort(Protocol):
    """Finds pages of catalogue domains for a fresh claim; it never fetches them.

    Features:
        US-KOR-04, US-WDR-02, F-13, ADR-07
    """

    async def search(
        self, query: MaskedText, *, limit: int = DEFAULT_RESULTS
    ) -> list[WebSearchCandidate]:
        """Search the web for ``query`` and keep only catalogue addresses.

        Args:
            query: the claim with personal data masked; nothing else is sent.
            limit: addresses asked from the provider, 1 to ``MAX_RESULTS``.

        Returns:
            Candidates in the provider's order, each from a catalogue domain,
            without duplicates; possibly fewer than ``limit``.

        Raises:
            ValueError: ``limit`` is outside 1 to ``MAX_RESULTS``.
            WebSearchTimeoutError: No answer within ``SEARCH_TIMEOUT_S``.
            WebSearchRateLimitError: Over the query limit or the provider's quota.
            WebSearchUnavailableError: The provider failed.
        """
        ...


class WebSearchProviderPort(Protocol):
    """One search provider: a query in, result addresses out, unfiltered.

    Features:
        US-KOR-04, US-WDR-02, F-13
    """

    async def search(self, query: str, *, limit: int) -> list[str]:
        """Return up to ``limit`` result addresses, best first.

        Args:
            query: the masked claim text.
            limit: most addresses to return, at least 1.

        Returns:
            Absolute result URLs as the provider gives them.

        Raises:
            WebSearchTimeoutError: The provider did not answer in time.
            WebSearchRateLimitError: The provider refused over quota.
            WebSearchUnavailableError: Any other provider failure.
        """
        ...
