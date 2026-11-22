"""Steps for the fallback web search scenarios of features/corpus.feature.

SearXNG answers from a recorded JSON reply through an in-process httpx2
transport; the environment is patched per scenario. Nothing leaves the process.
"""

import asyncio
import os
from pathlib import Path
from unittest import mock

import httpx2
from behave import given, then, when
from behave.runner import Context
from pydantic import ValidationError

from meritum_core.checks.contracts import CatalogEntry
from meritum_core.corpus.web_search import WebSearchSettings, build_web_search
from meritum_core.security import MaskedText

REPLY = (
    Path(__file__).parents[2] / "tests/corpus/web_search/fixtures/searxng-reply.json"
)
OUTSIDE = "https://example.com/burze"
LINKUP_CASES = (
    ({}, "MERITUM_WEB_SEARCH_LINKUP_API_KEY"),
    (
        {"MERITUM_WEB_SEARCH_LINKUP_API_KEY": "recorded"},
        "MERITUM_WEB_SEARCH_LINKUP_ENABLED",
    ),
)


def _entry(domain: str, publisher_id: str) -> CatalogEntry:
    return CatalogEntry.model_validate(
        {
            "domain": domain,
            "publisher": f"Wydawca {domain}",
            "publisher_id": publisher_id,
            "kind": "instytucja",
            "tier": "primary",
            "license": "materiał urzędowy",
            "ingest": "web_search",
            "qualified_because": "Komunikaty urzędowe dla obywateli.",
        }
    )


def _patch_env(context: Context, values: dict[str, str]) -> None:
    patcher = mock.patch.dict(os.environ, values)
    patcher.start()
    context.add_cleanup(patcher.stop)


@given("MERITUM_WEB_SEARCH_PROVIDER=searxng i adres instancji SearXNG")
def given_searxng(context: Context) -> None:
    """The environment names SearXNG and its address."""
    _patch_env(
        context,
        {
            "MERITUM_WEB_SEARCH_PROVIDER": "searxng",
            "MERITUM_WEB_SEARCH_SEARXNG_URL": "http://searxng:8080",
        },
    )


@when('fabryka buduje adapter i system szuka w sieci "{phrase}"')
def when_build_and_search(context: Context, phrase: str) -> None:
    """Build from the environment and search, recording the request."""
    context.sent = []

    def reply(request: httpx2.Request) -> httpx2.Response:
        context.sent.append(request)
        return httpx2.Response(200, content=REPLY.read_bytes())

    client = httpx2.AsyncClient(transport=httpx2.MockTransport(reply))
    catalog = (_entry("gov.pl", "gov"), _entry("meteo.imgw.pl", "imgw"))
    search = build_web_search(WebSearchSettings(), catalog, http_client=client)
    query = MaskedText(text=phrase, replaced=0)
    context.candidates = asyncio.run(search.search(query))


@then(
    "zapytanie jest ograniczone do domen katalogu,"
    " a wynik spoza katalogu odpada w naszym filtrze"
)
def then_limited_and_filtered(context: Context) -> None:
    """The query names catalogue sites; the outside result does not come back."""
    [request] = context.sent
    assert request.url.params["q"].endswith("(site:gov.pl OR site:meteo.imgw.pl)")
    urls = [c.url for c in context.candidates]
    assert urls
    assert OUTSIDE not in urls


@given("MERITUM_WEB_SEARCH_PROVIDER=linkup bez klucza albo z wyłączonym wyłącznikiem")
def given_linkup_misconfigured(context: Context) -> None:
    """Linkup without a key, and Linkup with a key but the switch off."""
    context.cases = LINKUP_CASES


@when("fabryka buduje adapter wyszukiwania")
def when_build_search(context: Context) -> None:
    """Build from each environment and keep the configuration error."""
    context.errors = []
    for extra, variable in context.cases:
        values = {"MERITUM_WEB_SEARCH_PROVIDER": "linkup", **extra}
        with mock.patch.dict(os.environ, values, clear=True):
            try:
                build_web_search(WebSearchSettings(), ())
            except ValidationError as error:
                context.errors.append((str(error), variable))
            else:
                context.errors.append(("", variable))


@then("zgłasza błąd konfiguracji, który test gotowości wymienia z nazwy zmiennej")
def then_error_names_variable(context: Context) -> None:
    """Each error names the variable that is missing or off."""
    assert len(context.errors) == len(LINKUP_CASES)
    for message, variable in context.errors:
        assert variable in message
