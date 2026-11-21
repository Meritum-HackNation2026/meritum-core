"""Vertex AI Search adapter over REST: basic website search in the ``global`` location.

The website data store, its INCLUDE patterns for the catalogue domains and the
search app are created by Terraform in meritum-infra (infra#16). The adapter
sends only the masked claim and reads result addresses; it never reads pages.

Features:
    US-KOR-04, US-WDR-02, F-13, ADR-07, ADR-14
"""

import asyncio

from google.auth import default as adc_lookup
from google.auth.credentials import Credentials
from google.auth.exceptions import GoogleAuthError
from google.auth.transport.requests import Request
from httpx2 import AsyncClient, TimeoutException, TransportError, codes
from pydantic import BaseModel, Field, ValidationError

from meritum_core.corpus.web_search.constants import (
    SEARCH_TIMEOUT_S,
    VERTEX_COLLECTION,
    VERTEX_ENDPOINT,
    VERTEX_LOCATION,
    VERTEX_SCOPES,
    VERTEX_SERVING_CONFIG,
)
from meritum_core.corpus.web_search.errors import (
    WebSearchRateLimitError,
    WebSearchTimeoutError,
    WebSearchUnavailableError,
)


class _Derived(BaseModel):
    link: str | None = None


class _Document(BaseModel):
    derived: _Derived = Field(default_factory=_Derived, alias="derivedStructData")


class _Result(BaseModel):
    document: _Document = Field(default_factory=_Document)


class _SearchResponse(BaseModel):
    results: list[_Result] = []


class VertexWebSearch:
    """WebSearchProviderPort on Vertex AI Search (Discovery Engine v1 ``:search``).

    Args:
        project: Google Cloud project of the search app.
        engine: id of the search app over the website data store.
        credentials: Google credentials; Application Default Credentials when None.
        http_client: HTTP client to use; tests pass one with recorded replies.

    Features:
        US-KOR-04, US-WDR-02, F-13, ADR-07, ADR-14
    """

    def __init__(
        self,
        project: str,
        engine: str,
        *,
        credentials: Credentials | None = None,
        http_client: AsyncClient | None = None,
    ) -> None:
        self._credentials = credentials
        self._client = http_client or AsyncClient(timeout=SEARCH_TIMEOUT_S)
        self._url = (
            f"{VERTEX_ENDPOINT}/projects/{project}/locations/{VERTEX_LOCATION}"
            f"/collections/{VERTEX_COLLECTION}/engines/{engine}"
            f"/servingConfigs/{VERTEX_SERVING_CONFIG}:search"
        )

    async def search(self, query: str, *, limit: int) -> list[str]:
        """Run one basic website search and return the result links.

        Args:
            query: the masked claim text.
            limit: ``pageSize`` of the request.

        Returns:
            ``derivedStructData.link`` of each result, in ranking order.

        Raises:
            WebSearchTimeoutError: The HTTP call timed out.
            WebSearchRateLimitError: The provider answered 429 (quota).
            WebSearchUnavailableError: Refused credentials, a transport error,
                any other error status, or a reply that does not parse.
        """
        headers = {"Authorization": f"Bearer {await self._token()}"}
        body = {"query": query, "pageSize": limit}
        try:
            response = await self._client.post(self._url, json=body, headers=headers)
        except TimeoutException as exc:
            msg = "vertex ai search timed out"
            raise WebSearchTimeoutError(msg) from exc
        except TransportError as exc:
            msg = f"vertex ai search unreachable: {type(exc).__name__}"
            raise WebSearchUnavailableError(msg) from exc
        if response.status_code == codes.TOO_MANY_REQUESTS:
            msg = "vertex ai search quota exceeded (HTTP 429)"
            raise WebSearchRateLimitError(msg)
        if not response.is_success:
            msg = f"vertex ai search failed: HTTP {response.status_code}"
            raise WebSearchUnavailableError(msg)
        try:
            reply = _SearchResponse.model_validate_json(response.content)
        except ValidationError as exc:
            msg = "vertex ai search reply is not a SearchResponse"
            raise WebSearchUnavailableError(msg) from exc
        links = (r.document.derived.link for r in reply.results)
        return [link for link in links if link is not None][:limit]

    async def _token(self) -> str:
        try:
            if self._credentials is None:
                self._credentials, _ = await asyncio.to_thread(
                    adc_lookup, scopes=VERTEX_SCOPES
                )
            credentials = self._credentials
            if not credentials.valid:
                await asyncio.to_thread(credentials.refresh, Request())
        except GoogleAuthError as exc:
            msg = "vertex ai search credentials were refused"
            raise WebSearchUnavailableError(msg) from exc
        return str(credentials.token)
