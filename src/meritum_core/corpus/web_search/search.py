"""The web search every provider answers through: limits first, catalogue filter last.

Features:
    US-KOR-04, US-WDR-02, F-13, ADR-07
"""

import asyncio
import time
from collections import deque
from collections.abc import Sequence

from meritum_core.checks.contracts import CatalogEntry
from meritum_core.corpus.web_search.constants import (
    DEFAULT_RESULTS,
    MAX_QUERIES_PER_MINUTE,
    MAX_RESULTS,
    RATE_WINDOW_S,
    SEARCH_TIMEOUT_S,
)
from meritum_core.corpus.web_search.domains import catalog_entry_for
from meritum_core.corpus.web_search.errors import (
    WebSearchRateLimitError,
    WebSearchTimeoutError,
)
from meritum_core.corpus.web_search.models import WebSearchCandidate
from meritum_core.corpus.web_search.ports import WebSearchProviderPort
from meritum_core.security import MaskedText


class CatalogWebSearch:
    """WebSearchPort over one provider, limited to the catalogue's domains.

    Args:
        provider: the adapter that asks the search engine.
        catalog: the loaded catalogue; addresses outside it are dropped.

    Features:
        US-KOR-04, US-WDR-02, F-13, ADR-07
    """

    def __init__(
        self, provider: WebSearchProviderPort, catalog: Sequence[CatalogEntry]
    ) -> None:
        self._provider = provider
        self._catalog = tuple(catalog)
        self._sent: deque[float] = deque()

    async def search(
        self, query: MaskedText, *, limit: int = DEFAULT_RESULTS
    ) -> list[WebSearchCandidate]:
        """Ask the provider and keep catalogue addresses, first occurrence only.

        Args:
            query: the claim with personal data masked; only its text is sent.
            limit: addresses asked from the provider, 1 to ``MAX_RESULTS``.

        Returns:
            Catalogue candidates in the provider's order.

        Raises:
            ValueError: ``limit`` is outside 1 to ``MAX_RESULTS``.
            WebSearchTimeoutError: No answer within ``SEARCH_TIMEOUT_S``.
            WebSearchRateLimitError: Over ``MAX_QUERIES_PER_MINUTE``.
        """  # ruff: ignore[docstring-extraneous-exception]  # the provider raises the other WebSearchErrors
        if not 1 <= limit <= MAX_RESULTS:
            msg = f"limit must be 1 to {MAX_RESULTS}"
            raise ValueError(msg)
        self._take_slot()
        try:
            async with asyncio.timeout(SEARCH_TIMEOUT_S):
                urls = await self._provider.search(query.text, limit=limit)
        except TimeoutError as exc:
            msg = f"no answer in {SEARCH_TIMEOUT_S} s"
            raise WebSearchTimeoutError(msg) from exc
        return self._candidates(urls)

    def _take_slot(self) -> None:
        now = time.monotonic()
        while self._sent and now - self._sent[0] >= RATE_WINDOW_S:
            self._sent.popleft()
        if len(self._sent) >= MAX_QUERIES_PER_MINUTE:
            msg = f"over {MAX_QUERIES_PER_MINUTE} searches per minute"
            raise WebSearchRateLimitError(msg)
        self._sent.append(now)

    def _candidates(self, urls: list[str]) -> list[WebSearchCandidate]:
        seen: set[str] = set()
        candidates: list[WebSearchCandidate] = []
        for url in urls:
            entry = catalog_entry_for(url, self._catalog)
            if entry is None or url in seen:
                continue
            seen.add(url)
            candidates.append(
                WebSearchCandidate(
                    url=url, domain=entry.domain, publisher_id=entry.publisher_id
                )
            )
        return candidates
