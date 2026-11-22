"""SearXNG and Linkup on recorded replies: request, catalogue limits, errors; no network."""

import asyncio
import json

import httpx2
import pytest
from pydantic import SecretStr, ValidationError

from meritum_core.checks.contracts import CatalogEntry
from meritum_core.corpus.web_search import (
    WebSearchPort,
    WebSearchProvider,
    WebSearchRateLimitError,
    WebSearchSettings,
    WebSearchTimeoutError,
    WebSearchUnavailableError,
    build_web_search,
    provider_contract_violations,
)
from meritum_core.corpus.web_search.adapters import LinkupWebSearch, SearxngWebSearch
from meritum_core.security import MaskedText

from .conftest import FIXTURES, Sent

QUERY = MaskedText(text="ostrzeżenie przed burzami", replaced=0)
SEARXNG: dict[str, object] = {
    "provider": "searxng",
    "searxng_url": "http://searxng:8080/",
}
LINKUP: dict[str, object] = {
    "provider": "linkup",
    "linkup_api_key": "recorded",
    "linkup_enabled": True,
}
REPLIES = {"searxng": "searxng-reply.json", "linkup": "linkup-reply.json"}
HOSTS = ("gov.pl", "meteo.imgw.pl")


def _client(status: int, name: str) -> tuple[httpx2.AsyncClient, Sent]:
    sent: Sent = []

    def reply(request: httpx2.Request) -> httpx2.Response:
        sent.append(request)
        return httpx2.Response(status, content=(FIXTURES / name).read_bytes())

    return httpx2.AsyncClient(transport=httpx2.MockTransport(reply)), sent


def _build(
    config: dict[str, object],
    catalog: tuple[CatalogEntry, ...],
    status: int = 200,
    name: str | None = None,
) -> tuple[WebSearchPort, Sent]:
    settings = WebSearchSettings.model_validate(config)
    client, sent = _client(status, name or REPLIES[settings.provider])
    return build_web_search(settings, catalog, http_client=client), sent


def test_searxng_query_is_limited_to_catalogue_hosts(
    catalog: tuple[CatalogEntry, ...],
) -> None:
    search, sent = _build(SEARXNG, catalog)
    candidates = asyncio.run(search.search(QUERY))
    [request] = sent
    assert request.method == "GET"
    assert str(request.url).startswith("http://searxng:8080/search?")
    assert request.url.params["format"] == "json"
    assert request.url.params["q"] == (
        "ostrzeżenie przed burzami (site:gov.pl OR site:meteo.imgw.pl)"
    )
    assert [c.url for c in candidates] == [
        "https://www.gov.pl/web/gov/ostrzezenia",
        "https://meteo.imgw.pl/dyn/?osmet=true",
    ]


def test_linkup_sends_catalogue_hosts_as_include_domains(
    catalog: tuple[CatalogEntry, ...],
) -> None:
    search, sent = _build(LINKUP, catalog)
    candidates = asyncio.run(search.search(QUERY, limit=5))
    [request] = sent
    assert str(request.url) == "https://api.linkup.so/v1/search"
    assert request.headers["authorization"] == "Bearer recorded"
    assert json.loads(request.content) == {
        "q": "ostrzeżenie przed burzami",
        "depth": "standard",
        "outputType": "searchResults",
        "includeDomains": list(HOSTS),
        "maxResults": 5,
    }
    assert "https://example.com/burze" not in [c.url for c in candidates]


@pytest.mark.parametrize("provider", ["searxng", "linkup"])
def test_adapters_keep_the_port_contract(provider: str) -> None:
    client, _ = _client(200, REPLIES[provider])
    adapter = (
        SearxngWebSearch("http://searxng:8080", HOSTS, http_client=client)
        if provider == "searxng"
        else LinkupWebSearch(SecretStr("recorded"), HOSTS, http_client=client)
    )
    assert asyncio.run(provider_contract_violations(adapter)) == []


@pytest.mark.parametrize("config", [SEARXNG, LINKUP])
@pytest.mark.parametrize(
    ("status", "name", "expected"),
    [
        (429, "quota.json", WebSearchRateLimitError),
        (503, "unavailable.json", WebSearchUnavailableError),
        (200, "not-a-reply.json", WebSearchUnavailableError),
    ],
)
def test_failures_map_to_documented_errors(
    catalog: tuple[CatalogEntry, ...],
    config: dict[str, object],
    status: int,
    name: str,
    expected: type[Exception],
) -> None:
    search, _ = _build(config, catalog, status, name)
    with pytest.raises(expected) as caught:
        asyncio.run(search.search(QUERY))
    assert "burzami" not in str(caught.value)


def test_searxng_timeout_is_a_timeout_error() -> None:
    def silent(request: httpx2.Request) -> httpx2.Response:
        msg = "no reply"
        raise httpx2.ReadTimeout(msg, request=request)

    client = httpx2.AsyncClient(transport=httpx2.MockTransport(silent))
    settings = WebSearchSettings.model_validate(SEARXNG)
    search = build_web_search(settings, (), http_client=client)
    with pytest.raises(WebSearchTimeoutError):
        asyncio.run(search.search(QUERY))


@pytest.mark.parametrize(
    ("config", "variable"),
    [
        ({"provider": "searxng"}, "MERITUM_WEB_SEARCH_SEARXNG_URL"),
        (
            {"provider": "linkup", "linkup_enabled": True},
            "MERITUM_WEB_SEARCH_LINKUP_API_KEY",
        ),
        (
            {"provider": "linkup", "linkup_api_key": "k"},
            "MERITUM_WEB_SEARCH_LINKUP_ENABLED",
        ),
    ],
)
def test_missing_configuration_names_the_variable(
    config: dict[str, object], variable: str
) -> None:
    with pytest.raises(ValidationError, match=variable):
        WebSearchSettings.model_validate(config)


@pytest.mark.parametrize(
    "settings",
    [
        WebSearchSettings.model_construct(provider=WebSearchProvider.SEARXNG),
        WebSearchSettings.model_construct(
            provider=WebSearchProvider.LINKUP, linkup_api_key=SecretStr("k")
        ),
    ],
)
def test_factory_refuses_unvalidated_fallback_settings(
    settings: WebSearchSettings,
) -> None:
    with pytest.raises(ValueError, match="MERITUM_WEB_SEARCH_"):
        build_web_search(settings, ())
