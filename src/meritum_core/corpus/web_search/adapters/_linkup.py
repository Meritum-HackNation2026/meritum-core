"""Linkup adapter: optional paid search, built only with a key and the switch on.

Linkup gets the catalogue hosts in ``includeDomains``; ``catalog_entry_for``
still filters the reply.

Features:
    US-KOR-04, US-WDR-02, F-13, ADR-07
"""

from collections.abc import Sequence

from httpx2 import AsyncClient
from pydantic import BaseModel, SecretStr, ValidationError

from meritum_core.corpus.web_search.adapters._http import checked_reply
from meritum_core.corpus.web_search.constants import (
    LINKUP_DEPTH,
    LINKUP_ENDPOINT,
    LINKUP_OUTPUT,
    SEARCH_TIMEOUT_S,
)
from meritum_core.corpus.web_search.errors import WebSearchUnavailableError


class _Result(BaseModel):
    url: str | None = None


class _Reply(BaseModel):
    results: list[_Result]


class LinkupWebSearch:
    """WebSearchProviderPort on Linkup ``/v1/search`` with ``searchResults`` output.

    Args:
        api_key: the Linkup key, sent as a bearer token.
        hosts: catalogue hosts sent as ``includeDomains`` (``catalog_hosts``).
        http_client: HTTP client to use; tests pass one with recorded replies.

    Features:
        US-KOR-04, US-WDR-02, F-13, ADR-07
    """

    def __init__(
        self,
        api_key: SecretStr,
        hosts: Sequence[str],
        *,
        http_client: AsyncClient | None = None,
    ) -> None:
        self._key = api_key
        self._hosts = list(hosts)
        self._client = http_client or AsyncClient(timeout=SEARCH_TIMEOUT_S)

    async def search(self, query: str, *, limit: int) -> list[str]:
        """Ask Linkup for the query on catalogue hosts and return result URLs.

        Args:
            query: the masked claim text.
            limit: ``maxResults`` of the request.

        Returns:
            Result URLs in Linkup's order.

        Raises:
            WebSearchUnavailableError: A reply that is not Linkup search results.
        """
        body = {
            "q": query,
            "depth": LINKUP_DEPTH,
            "outputType": LINKUP_OUTPUT,
            "includeDomains": self._hosts,
            "maxResults": limit,
        }
        headers = {"Authorization": f"Bearer {self._key.get_secret_value()}"}
        call = self._client.post(LINKUP_ENDPOINT, json=body, headers=headers)
        reply_body = await checked_reply("linkup", call)
        try:
            reply = _Reply.model_validate_json(reply_body)
        except ValidationError as exc:
            msg = "linkup reply is not search results"
            raise WebSearchUnavailableError(msg) from exc
        return [r.url for r in reply.results if r.url is not None][:limit]
