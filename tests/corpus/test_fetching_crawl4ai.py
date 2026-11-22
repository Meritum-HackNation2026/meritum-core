"""Pages that need JavaScript: rendered by Crawl4AI behind the same guards.

Crawl4AI answers come from recorded replies in ``fixtures/``; no browser, no network.
"""

import asyncio
import json
from pathlib import Path

import httpx
import pytest
from tests.corpus.conftest import ARTICLE, FakeDns

from meritum_core.corpus.fetching import (
    FetchedPage,
    FetchFailureReason,
    FetchingSettings,
    FetchPurpose,
    JavaScriptRequiredError,
    PageFetchError,
    build_page_fetcher,
)

FIXTURES = Path(__file__).parent / "fixtures"
URL = "https://example.org/app"
RENDERER = "http://crawl4ai:11235"
EMPTY = httpx.Response(200, html='<html><body><div id="root"></div></body></html>')

type Reply = dict[str, object]
type Dns = dict[str, list[list[str]]]
TOKEN = "s3cret"  # ruff: ignore[hardcoded-password-string]  # a test token for the fake service


def recorded(name: str, **result: str) -> object:
    reply = json.loads((FIXTURES / name).read_text(encoding="utf-8"))
    reply["results"][0].update(result)
    return reply


class Site:
    """The public site and the Crawl4AI service on one in-process transport."""

    def __init__(self, reply: object, robots: str = "") -> None:
        self.reply = reply
        self.robots = robots
        self.renders: list[Reply] = []

    def __call__(self, request: httpx.Request) -> httpx.Response:
        if request.url.host == "crawl4ai":
            assert request.headers["authorization"] == f"Bearer {TOKEN}"
            self.renders.append(json.loads(request.content))
            return httpx.Response(200, json=self.reply)
        if request.url.path == "/robots.txt":
            return (
                httpx.Response(200, text=self.robots)
                if self.robots
                else httpx.Response(404)
            )
        return EMPTY


def fetch(
    site: Site,
    *,
    dns: Dns | None = None,
    enabled: bool = True,
    purpose: FetchPurpose = FetchPurpose.USER_LINK,
) -> FetchedPage:
    settings = FetchingSettings(
        crawl4ai_url=RENDERER if enabled else None, crawl4ai_token=TOKEN
    )
    fetcher = build_page_fetcher(
        settings=settings,
        resolver=FakeDns(dns or {"example.org": [["93.184.215.14"]]}),
        transport=httpx.MockTransport(site),
    )
    return asyncio.run(fetcher.fetch(URL, purpose=purpose))


def failure(
    site: Site,
    *,
    dns: Dns | None = None,
    enabled: bool = True,
    purpose: FetchPurpose = FetchPurpose.USER_LINK,
) -> PageFetchError:
    with pytest.raises(PageFetchError) as caught:
        fetch(site, dns=dns, enabled=enabled, purpose=purpose)
    return caught.value


def test_page_without_main_text_is_rendered_by_crawl4ai() -> None:
    site = Site(recorded("crawl4ai-rendered.json"))
    page = fetch(site)
    assert page.untrusted_text.startswith(ARTICLE[12:40])
    assert (page.url, page.content_type) == (URL, "text/html")
    assert [r["urls"] for r in site.renders] == [[URL]]


def test_without_crawl4ai_the_documented_error_stays() -> None:
    site = Site(recorded("crawl4ai-rendered.json"))
    assert isinstance(failure(site, enabled=False), JavaScriptRequiredError)
    assert site.renders == []


def test_internal_address_never_reaches_crawl4ai() -> None:
    site = Site(recorded("crawl4ai-rendered.json"))
    error = failure(site, dns={"example.org": [["93.184.215.14"], ["10.0.0.7"]]})
    assert error.reason is FetchFailureReason.BLOCKED_ADDRESS
    assert site.renders == []


def test_robots_disallow_stops_the_render() -> None:
    site = Site(recorded("crawl4ai-rendered.json"), robots="User-agent: *\nDisallow: /")
    error = failure(site, purpose=FetchPurpose.SOURCE)
    assert error.reason is FetchFailureReason.ROBOTS_DISALLOWED
    assert site.renders == []


@pytest.mark.parametrize(
    ("final", "dns"),
    [
        ("https://other.example/app", {}),
        (
            "https://example.org/app",
            {"example.org": [["93.184.215.14"]] * 2 + [["127.0.0.1"]]},
        ),
        ("http://169.254.169.254/latest/meta-data", {}),
    ],
)
def test_render_that_lands_elsewhere_is_discarded(final: str, dns: Dns) -> None:
    site = Site(recorded("crawl4ai-rendered.json", redirected_url=final))
    table = {"example.org": [["93.184.215.14"]], **dns}
    error = failure(site, dns=table)
    assert error.reason is FetchFailureReason.REDIRECT_BLOCKED


def test_failed_render_is_unreachable() -> None:
    error = failure(Site(recorded("crawl4ai-failed.json")))
    assert error.reason is FetchFailureReason.UNREACHABLE
    assert str(error) == "unreachable"  # never the provider's error text


def test_rendered_page_without_text_still_needs_javascript() -> None:
    site = Site(recorded("crawl4ai-rendered.json", html="<html><body></body></html>"))
    assert isinstance(failure(site), JavaScriptRequiredError)
