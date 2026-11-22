"""SearXNG adapter: our own metasearch instance, the fallback of Vertex AI Search.

The query carries ``site:`` operators for the catalogue hosts, so the engines
behind SearXNG search only there; ``catalog_entry_for`` still filters the reply.

Features:
    US-KOR-04, US-WDR-02, F-13, ADR-07
"""

from collections.abc import Sequence

from httpx2 import AsyncClient
from pydantic import BaseModel, ValidationError

from meritum_core.corpus.web_search.adapters._http import checked_reply
from meritum_core.corpus.web_search.constants import (
    SEARCH_TIMEOUT_S,
    SEARXNG_FORMAT,
    SEARXNG_SEARCH_PATH,
    SITE_JOINER,
)
from meritum_core.corpus.web_search.errors import WebSearchUnavailableError


class _Result(BaseModel):
    url: str | None = None


class _Reply(BaseModel):
    results: list[_Result]


class SearxngWebSearch:
    """WebSearchProviderPort on a SearXNG instance (``/search?format=json``).

    Args:
        base_url: address of the instance, e.g. ``http://searxng:8080/``.
        hosts: catalogue hosts the query is limited to (``catalog_hosts``).
        http_client: HTTP client to use; tests pass one with recorded replies.

    Features:
        US-KOR-04, US-WDR-02, F-13, ADR-07
    """

    def __init__(
        self,
        base_url: str,
        hosts: Sequence[str],
        *,
        http_client: AsyncClient | None = None,
    ) -> None:
        self._url = f"{base_url.rstrip('/')}/{SEARXNG_SEARCH_PATH}"
        self._sites = SITE_JOINER.join(f"site:{host}" for host in hosts)
        self._client = http_client or AsyncClient(timeout=SEARCH_TIMEOUT_S)

    async def search(self, query: str, *, limit: int) -> list[str]:
        """Ask SearXNG for the query on catalogue hosts and return result URLs.

        Args:
            query: the masked claim text.
            limit: most addresses to return; the SearXNG page is cut to it.

        Returns:
            Result URLs in SearXNG's ranking order.

        Raises:
            WebSearchUnavailableError: A reply that is not SearXNG JSON.
        """
        q = f"{query} ({self._sites})" if self._sites else query
        call = self._client.get(self._url, params={"q": q, "format": SEARXNG_FORMAT})
        body = await checked_reply("searxng", call)
        try:
            reply = _Reply.model_validate_json(body)
        except ValidationError as exc:
            msg = "searxng reply is not search JSON"
            raise WebSearchUnavailableError(msg) from exc
        return [r.url for r in reply.results if r.url is not None][:limit]
