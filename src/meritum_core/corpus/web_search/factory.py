"""Builds live web search from ``MERITUM_WEB_SEARCH_*``; only it builds the adapters.

Features:
    US-KOR-04, US-WDR-02, F-13, ADR-07
"""

from collections.abc import Sequence

from google.auth.credentials import Credentials
from httpx2 import AsyncClient
from pydantic import TypeAdapter

from meritum_core.checks.contracts import CatalogEntry
from meritum_core.corpus.web_search.adapters import (
    LinkupWebSearch,
    SearxngWebSearch,
    StubWebSearch,
    VertexWebSearch,
)
from meritum_core.corpus.web_search.domains import catalog_hosts
from meritum_core.corpus.web_search.ports import WebSearchPort, WebSearchProviderPort
from meritum_core.corpus.web_search.search import CatalogWebSearch
from meritum_core.corpus.web_search.settings import (
    WebSearchProvider,
    WebSearchSettings,
)


def _vertex(
    settings: WebSearchSettings,
    credentials: Credentials | None,
    http_client: AsyncClient | None,
) -> WebSearchProviderPort:
    if settings.project is None or settings.engine is None:
        msg = "vertex_search needs a project and an engine"
        raise ValueError(msg)
    return VertexWebSearch(
        settings.project,
        settings.engine,
        credentials=credentials,
        http_client=http_client,
    )


def _fallback(
    settings: WebSearchSettings,
    hosts: tuple[str, ...],
    http_client: AsyncClient | None,
) -> WebSearchProviderPort:
    if settings.provider is WebSearchProvider.SEARXNG:
        if settings.searxng_url is None:
            msg = "searxng needs MERITUM_WEB_SEARCH_SEARXNG_URL"
            raise ValueError(msg)
        url = str(settings.searxng_url)
        return SearxngWebSearch(url, hosts, http_client=http_client)
    if settings.linkup_api_key is None or not settings.linkup_enabled:
        msg = "linkup needs MERITUM_WEB_SEARCH_LINKUP_API_KEY and _LINKUP_ENABLED"
        raise ValueError(msg)
    return LinkupWebSearch(settings.linkup_api_key, hosts, http_client=http_client)


def _provider(
    settings: WebSearchSettings,
    catalog: Sequence[CatalogEntry],
    credentials: Credentials | None,
    http_client: AsyncClient | None,
) -> WebSearchProviderPort:
    match settings.provider:
        case WebSearchProvider.VERTEX_SEARCH:
            return _vertex(settings, credentials, http_client)
        case WebSearchProvider.SEARXNG | WebSearchProvider.LINKUP:
            return _fallback(settings, catalog_hosts(catalog), http_client)
        case WebSearchProvider.STUB:
            path = settings.stub_fixture
            urls = (
                TypeAdapter(list[str]).validate_json(path.read_bytes()) if path else []
            )
            return StubWebSearch(urls)


def build_web_search(
    settings: WebSearchSettings,
    catalog: Sequence[CatalogEntry],
    *,
    credentials: Credentials | None = None,
    http_client: AsyncClient | None = None,
) -> WebSearchPort:
    """Build the provider the settings name, behind the catalogue filter and limits.

    Args:
        settings: Usually ``WebSearchSettings()`` from the environment.
        catalog: The loaded catalogue (``load_catalog()``); only its domains pass,
            and SearXNG and Linkup are asked to search only its hosts.
        credentials: Google credentials for Vertex AI Search; Application
            Default Credentials when None. Ignored by the other providers.
        http_client: HTTP client for Vertex AI Search, SearXNG or Linkup (shared
            pool, or recorded replies in tests); a new one when None.

    Returns:
        The web search port.

    Raises:
        ValueError: A provider without its required settings (settings built
            unvalidated): vertex_search without a project or engine, searxng
            without an address, linkup without a key or with the switch off.
        ValidationError: The stub fixture is not a JSON list of strings.

    Features:
        US-KOR-04, US-WDR-02, F-13, ADR-07
    """  # ruff: ignore[docstring-extraneous-exception]  # raised by _provider
    provider = _provider(settings, catalog, credentials, http_client)
    return CatalogWebSearch(provider, catalog)
