"""Stub provider: result addresses from a fixture, no keys and no network.

Features:
    US-KOR-04, US-WDR-02, F-13
"""

from collections.abc import Sequence


class StubWebSearch:
    """WebSearchProviderPort answering every query with the same addresses.

    Args:
        urls: the addresses to return, best first.

    Features:
        US-KOR-04, US-WDR-02, F-13
    """

    def __init__(self, urls: Sequence[str]) -> None:
        self._urls = tuple(urls)

    async def search(self, query: str, *, limit: int) -> list[str]:
        """Return the first ``limit`` fixture addresses, whatever the query.

        Args:
            query: ignored.
            limit: most addresses to return.

        Returns:
            The fixture's addresses.
        """
        del query
        return list(self._urls[:limit])
