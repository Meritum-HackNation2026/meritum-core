"""Page fetcher publication date: read from the HTML metadata by trafilatura."""

import asyncio
from datetime import date
from typing import TYPE_CHECKING

import httpx
import pytest

from meritum_core.corpus.fetching import FetchedPage, FetchPurpose

if TYPE_CHECKING:
    from tests.corpus.conftest import Route, Web

URL = "https://example.org/post"


def fetch(web: Web, route: Route) -> FetchedPage:
    fetcher, _ = web.build({"example.org/post": route})
    return asyncio.run(fetcher.fetch(URL, purpose=FetchPurpose.USER_LINK))


def page(head: str, body: str) -> Route:
    html = f"<html><head>{head}</head><body>{body}</body></html>"
    return lambda _: httpx.Response(200, html=html)


@pytest.mark.parametrize(
    "head",
    [
        '<meta property="article:published_time" content="2026-11-18T09:30:00+01:00">',
        (
            '<script type="application/ld+json">'
            '{"@type": "NewsArticle", "datePublished": "2026-11-18"}</script>'
        ),
    ],
    ids=["open-graph", "json-ld"],
)
def test_publication_date_is_read_from_metadata(web: Web, head: str) -> None:
    assert fetch(web, page(head, web.article)).published_at == date(2026, 11, 18)


def test_page_without_a_date_has_no_publication_date(web: Web) -> None:
    assert fetch(web, page("", web.article)).published_at is None


def test_unreadable_date_is_dropped_and_the_text_kept(web: Web) -> None:
    head = '<meta property="article:published_time" content="kiedyś">'
    fetched = fetch(web, page(head, web.article))
    assert fetched.published_at is None
    assert fetched.untrusted_text.startswith("Sejm uchwalił")


def test_plain_text_has_no_publication_date(web: Web) -> None:
    def plain(_: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text="Komunikat z 2026-11-18.")

    assert fetch(web, plain).published_at is None


def test_page_built_without_a_date_defaults_to_none() -> None:
    built = FetchedPage(url=URL, content_type="text/plain", untrusted_text="Komunikat.")
    assert built.published_at is None
