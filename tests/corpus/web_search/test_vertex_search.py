"""Vertex AI Search on recorded replies: request, parsing and errors; no network."""

import asyncio
import json

import httpx2
import pytest
from google.oauth2.credentials import Credentials

from meritum_core.corpus.web_search import (
    WebSearchRateLimitError,
    WebSearchSettings,
    WebSearchTimeoutError,
    WebSearchUnavailableError,
    build_web_search,
)
from meritum_core.security import MaskedText

from .conftest import Recorded

SEARCH_URL = (
    "https://discoveryengine.googleapis.com/v1/projects/meritum-test/locations/global"
    "/collections/default_collection/engines/meritum-web"
    "/servingConfigs/default_search:search"
)
QUERY = MaskedText(text="Burza w [MIEJSCE] jutro", replaced=1)


def test_only_the_masked_claim_goes_to_the_search_app(recorded: Recorded) -> None:
    search, sent = recorded(200, "search-reply.json")
    asyncio.run(search.search(QUERY, limit=5))
    [request] = sent
    assert request.method == "POST"
    assert str(request.url) == SEARCH_URL
    assert request.headers["authorization"] == "Bearer recorded"
    assert json.loads(request.content) == {
        "query": "Burza w [MIEJSCE] jutro",
        "pageSize": 5,
    }


def test_result_links_become_catalogue_candidates(recorded: Recorded) -> None:
    search, _ = recorded(200, "search-reply.json")
    candidates = asyncio.run(search.search(QUERY))
    assert [(c.url, c.domain, c.publisher_id) for c in candidates] == [
        (
            "https://www.gov.pl/web/gov/ostrzezenia",
            "www.gov.pl/web/gov/ostrzezenia",
            "rcb",
        ),
        ("https://meteo.imgw.pl/dyn/?osmet=true", "meteo.imgw.pl", "imgw"),
    ]


def test_quota_reply_is_a_rate_limit_error(recorded: Recorded) -> None:
    search, _ = recorded(429, "quota.json")
    with pytest.raises(WebSearchRateLimitError) as caught:
        asyncio.run(search.search(QUERY))
    assert caught.value.check_status == "technical_failure"


@pytest.mark.parametrize(
    ("status", "name"), [(503, "unavailable.json"), (200, "not-a-reply.json")]
)
def test_failed_or_garbled_reply_is_unavailable(
    recorded: Recorded, status: int, name: str
) -> None:
    search, _ = recorded(status, name)
    with pytest.raises(WebSearchUnavailableError) as caught:
        asyncio.run(search.search(QUERY))
    assert "Burza" not in str(caught.value)


@pytest.mark.parametrize(
    ("raised", "expected"),
    [
        (httpx2.ReadTimeout, WebSearchTimeoutError),
        (httpx2.ConnectError, WebSearchUnavailableError),
    ],
)
def test_transport_failures_map_to_documented_errors(
    raised: type[httpx2.TransportError], expected: type[Exception]
) -> None:
    def fail(request: httpx2.Request) -> httpx2.Response:
        msg = "recorded failure"
        raise raised(msg, request=request)

    client = httpx2.AsyncClient(transport=httpx2.MockTransport(fail))
    token = Credentials(token="recorded")  # ruff: ignore[hardcoded-password-func-arg]  # fake token, no network
    settings = WebSearchSettings(
        provider="vertex_search", project="meritum-test", engine="meritum-web"
    )
    search = build_web_search(settings, (), credentials=token, http_client=client)
    with pytest.raises(expected):
        asyncio.run(search.search(QUERY))
