"""Steps for the live web search scenarios of features/corpus.feature.

The provider is the stub with a temporary fixture, or Vertex AI Search behind an
in-process httpx2 transport: nothing leaves the process.
"""

import asyncio
import json
import os
import shutil
import tempfile
from pathlib import Path
from unittest import mock

import httpx2
from behave import given, then, when
from behave.runner import Context
from google.oauth2.credentials import Credentials

from meritum_core.checks.contracts import CatalogEntry
from meritum_core.corpus.web_search import (
    WebSearchError,
    WebSearchSettings,
    WebSearchTimeoutError,
    build_web_search,
)
from meritum_core.security import MaskedText

GOV = "https://www.gov.pl/web/rcb/ostrzezenie-przed-burzami"
OUTSIDE = "https://example.com/burze"
FIXTURE_URLS = ["https://meteo.imgw.pl/ostrzezenia", GOV]


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


def _catalog() -> tuple[CatalogEntry, ...]:
    return (_entry("gov.pl", "gov"), _entry("imgw.pl", "imgw"))


def _fixture(context: Context, urls: list[str]) -> Path:
    folder = tempfile.mkdtemp()
    context.add_cleanup(shutil.rmtree, folder)
    fixture = Path(folder) / "results.json"
    fixture.write_text(json.dumps(urls), encoding="utf-8")
    return fixture


def _stub(context: Context, urls: list[str]) -> None:
    fixture = _fixture(context, urls)
    settings = WebSearchSettings(provider="stub", stub_fixture=fixture)
    context.search = build_web_search(settings, context.catalog)


def _set_env(context: Context, name: str, value: str) -> None:
    patcher = mock.patch.dict(os.environ, {name: value})
    patcher.start()
    context.add_cleanup(patcher.stop)


def _forbid_network(context: Context) -> None:
    """Record every socket connection and DNS lookup instead of making it."""
    context.network_calls = []

    def record(*args: object, **_: object) -> None:
        context.network_calls.append(args)
        msg = "network is forbidden in this scenario"
        raise OSError(msg)

    for target in ("socket.socket.connect", "socket.getaddrinfo"):
        patcher = mock.patch(target, record)
        patcher.start()
        context.add_cleanup(patcher.stop)


def _run(context: Context, phrase: str) -> None:
    query = MaskedText(text=phrase, replaced=0)
    try:
        context.candidates = asyncio.run(context.search.search(query))
    except WebSearchError as error:
        context.error = error
    else:
        context.error = None


@given("katalog z domenami gov.pl i imgw.pl")
def given_catalog_gov_imgw(context: Context) -> None:
    """Two catalogue domains, matched with their subdomains."""
    context.catalog = _catalog()


@given("dostawca zwraca adresy z gov.pl i z example.com")
def given_provider_mixed(context: Context) -> None:
    """The provider answers with one catalogue address and one from outside."""
    _stub(context, [OUTSIDE, GOV])


@when('system wyszukuje frazę "{phrase}"')
def when_search_phrase(context: Context, phrase: str) -> None:
    """Search the masked phrase."""
    _run(context, phrase)


@then("port zwraca tylko adres z gov.pl jako kandydata do pobrania")
def then_only_gov(context: Context) -> None:
    """One candidate: the gov.pl address with its catalogue publisher."""
    assert context.error is None
    [candidate] = context.candidates
    assert (candidate.url, candidate.domain, candidate.publisher_id) == (
        GOV,
        "gov.pl",
        "gov",
    )


@then("adres z example.com nie jest pobierany ani cytowany")
def then_outside_dropped(context: Context) -> None:
    """The outside address never reaches the caller, so nothing fetches it."""
    assert all(c.url != OUTSIDE for c in context.candidates)


@given("dostawca nie odpowiada przez 10 s")
def given_provider_silent(context: Context) -> None:
    """Vertex AI Search whose transport times out."""

    def silent(request: httpx2.Request) -> httpx2.Response:
        msg = "no reply"
        raise httpx2.ReadTimeout(msg, request=request)

    client = httpx2.AsyncClient(transport=httpx2.MockTransport(silent))
    settings = WebSearchSettings(
        provider="vertex_search", project="meritum-test", engine="meritum-web"
    )
    token = Credentials(token="recorded")  # ruff: ignore[hardcoded-password-func-arg]  # fake token, no network
    context.search = build_web_search(
        settings, _catalog(), credentials=token, http_client=client
    )


@when("system czeka na wynik wyszukiwania")
def when_wait_for_search(context: Context) -> None:
    """Search any phrase and keep the error."""
    _run(context, "ostrzeżenie przed burzami")


@then(
    "port rzuca udokumentowany błąd przekroczenia czasu,"
    ' który workflow mapuje na "{status}"'
)
def then_timeout_error(context: Context, status: str) -> None:
    """The documented timeout error, carrying the check status."""
    assert isinstance(context.error, WebSearchTimeoutError)
    assert context.error.check_status == status


@given("MERITUM_WEB_SEARCH_PROVIDER=stub")
def given_stub_provider(context: Context) -> None:
    """The environment names the stub and its fixture; the settings read it."""
    context.catalog = _catalog()
    _set_env(context, "MERITUM_WEB_SEARCH_PROVIDER", "stub")
    fixture = _fixture(context, FIXTURE_URLS)
    _set_env(context, "MERITUM_WEB_SEARCH_STUB_FIXTURE", str(fixture))
    _forbid_network(context)
    context.search = build_web_search(WebSearchSettings(), context.catalog)


@when("system wyszukuje dowolną frazę")
def when_search_any(context: Context) -> None:
    """Search any phrase."""
    _run(context, "dowolna fraza")


@then("port zwraca kandydatów z fixture, bez wywołań sieci")
def then_fixture_candidates(context: Context) -> None:
    """The fixture's addresses, in order, with no connection or DNS lookup."""
    assert context.error is None
    assert [c.url for c in context.candidates] == FIXTURE_URLS
    assert context.network_calls == []
