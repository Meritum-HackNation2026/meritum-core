"""The search every provider answers through: limits, timeout, dedupe, contract."""

import asyncio
import json
from pathlib import Path
from typing import override

import httpx2
import pytest
from google.oauth2.credentials import Credentials
from pydantic import ValidationError

from meritum_core.corpus.web_search import (
    WebSearchProviderPort,
    WebSearchRateLimitError,
    WebSearchSettings,
    WebSearchTimeoutError,
    build_web_search,
    provider_contract_violations,
)
from meritum_core.corpus.web_search.adapters import StubWebSearch, VertexWebSearch
from meritum_core.corpus.web_search.constants import MAX_QUERIES_PER_MINUTE
from meritum_core.corpus.web_search.search import CatalogWebSearch
from meritum_core.security import MaskedText

from .conftest import FIXTURES, entry

QUERY = MaskedText(text="ostrzeżenie przed burzami", replaced=0)
GOV = "https://www.gov.pl/web/rcb"
CATALOG = (entry("gov.pl", "gov"),)


def _stub(tmp_path: Path, urls: list[str]) -> WebSearchSettings:
    fixture = tmp_path / "results.json"
    fixture.write_text(json.dumps(urls), encoding="utf-8")
    return WebSearchSettings(provider="stub", stub_fixture=fixture)


def test_duplicate_addresses_come_once(tmp_path: Path) -> None:
    search = build_web_search(_stub(tmp_path, [GOV, GOV]), CATALOG)
    assert [c.url for c in asyncio.run(search.search(QUERY))] == [GOV]


def test_stub_without_fixture_finds_nothing() -> None:
    search = build_web_search(WebSearchSettings(), CATALOG)
    assert asyncio.run(search.search(QUERY)) == []


def test_stub_fixture_must_be_a_list_of_addresses(tmp_path: Path) -> None:
    fixture = tmp_path / "results.json"
    fixture.write_text('{"link": "x"}', encoding="utf-8")
    with pytest.raises(ValidationError):
        build_web_search(WebSearchSettings(stub_fixture=fixture), CATALOG)


@pytest.mark.parametrize("limit", [0, 26])
def test_limit_outside_the_provider_range_is_refused(limit: int) -> None:
    search = build_web_search(WebSearchSettings(), CATALOG)
    with pytest.raises(ValueError, match="limit"):
        asyncio.run(search.search(QUERY, limit=limit))


def test_searches_over_the_query_limit_are_refused(tmp_path: Path) -> None:
    search = build_web_search(_stub(tmp_path, [GOV]), CATALOG)

    async def burst() -> None:
        for _ in range(MAX_QUERIES_PER_MINUTE):
            await search.search(QUERY)
        await search.search(QUERY)

    with pytest.raises(WebSearchRateLimitError):
        asyncio.run(burst())


def test_slow_provider_times_out(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("meritum_core.corpus.web_search.search.SEARCH_TIMEOUT_S", 0.01)

    class Silent(StubWebSearch):
        @override
        async def search(self, query: str, *, limit: int) -> list[str]:
            await asyncio.sleep(1)
            return await super().search(query, limit=limit)

    search = CatalogWebSearch(Silent([GOV]), CATALOG)
    with pytest.raises(WebSearchTimeoutError) as caught:
        asyncio.run(search.search(QUERY))
    assert caught.value.check_status == "technical_failure"


@pytest.mark.parametrize(
    "settings",
    [
        {"provider": "vertex_search", "engine": "meritum-web"},
        {"provider": "vertex_search", "project": "meritum-test"},
        {"provider": "vertex_search", "project": "x/../y", "engine": "meritum-web"},
    ],
)
def test_vertex_needs_a_plain_project_and_engine(settings: dict[str, str]) -> None:
    with pytest.raises(ValidationError):
        WebSearchSettings.model_validate(settings)


def test_stub_keeps_the_provider_contract() -> None:
    provider: WebSearchProviderPort = StubWebSearch([GOV, "https://imgw.pl/"])
    assert asyncio.run(provider_contract_violations(provider)) == []


def test_contract_reports_a_broken_provider() -> None:
    provider: WebSearchProviderPort = StubWebSearch(["gov.pl/bez-schematu"])
    assert asyncio.run(provider_contract_violations(provider)) == [
        "returned an address that is not an absolute http(s) URL"
    ]


def test_vertex_keeps_the_provider_contract() -> None:
    reply = json.loads((FIXTURES / "search-reply.json").read_text(encoding="utf-8"))
    client = httpx2.AsyncClient(
        transport=httpx2.MockTransport(lambda _: httpx2.Response(200, json=reply))
    )
    token = Credentials(token="recorded")  # ruff: ignore[hardcoded-password-func-arg]  # fake token, no network
    provider = VertexWebSearch(
        "meritum-test", "meritum-web", credentials=token, http_client=client
    )
    assert asyncio.run(provider_contract_violations(provider)) == []
