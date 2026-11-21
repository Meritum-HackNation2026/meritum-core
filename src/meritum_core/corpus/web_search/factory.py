"""Builds live web search from ``MERITUM_WEB_SEARCH_*``; only it builds the adapters.

Features:
    US-KOR-04, US-WDR-02, F-13, ADR-07
"""

from collections.abc import Sequence

from google.auth.credentials import Credentials
from httpx2 import AsyncClient
from pydantic import TypeAdapter

from meritum_core.checks.contracts import CatalogEntry
from meritum_core.corpus.web_search.adapters import StubWebSearch, VertexWebSearch
from meritum_core.corpus.web_search.ports import WebSearchPort, WebSearchProviderPort
from meritum_core.corpus.web_search.search import CatalogWebSearch
from meritum_core.corpus.web_search.settings import (
    WebSearchProvider,
    WebSearchSettings,
)


def _provider(
    settings: WebSearchSettings,
    credentials: Credentials | None,
    http_client: AsyncClient | None,
) -> WebSearchProviderPort:
    match settings.provider:
        case WebSearchProvider.VERTEX_SEARCH:
            if settings.project is None or settings.engine is None:
                msg = "vertex_search needs a project and an engine"
                raise ValueError(msg)
            return VertexWebSearch(
                settings.project,
                settings.engine,
                credentials=credentials,
                http_client=http_client,
            )
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
        catalog: The loaded catalogue (``load_catalog()``); only its domains pass.
        credentials: Google credentials for Vertex AI Search; Application
            Default Credentials when None. Ignored by the stub.
        http_client: HTTP client for Vertex AI Search (shared pool, or recorded
            replies in tests); a new one when None. Ignored by the stub.

    Returns:
        The web search port.

    Raises:
        ValueError: vertex_search without a project or engine (settings built
            unvalidated).
        ValidationError: The stub fixture is not a JSON list of strings.

    Features:
        US-KOR-04, US-WDR-02, F-13, ADR-07
    """  # ruff: ignore[docstring-extraneous-exception]  # raised by _provider
    return CatalogWebSearch(_provider(settings, credentials, http_client), catalog)
