"""In-process fakes for the page fetcher: substituted DNS and an HTTP handler.

Tests get them through the ``web`` fixture (tests/ is not a package).
"""

import ipaddress
from collections.abc import Callable, Mapping

import httpx
import pytest

from meritum_core.corpus.fetching.adapters import HttpxPageFetcher

type Route = Callable[[httpx.Request], httpx.Response]
type Address = ipaddress.IPv4Address | ipaddress.IPv6Address


class FakeDns:
    """Answers from a table; each answer list is used in turn (DNS rebinding)."""

    def __init__(self, table: dict[str, list[list[str]]]) -> None:
        self.table = table
        self.lookups: list[str] = []

    async def __call__(self, host: str) -> list[Address]:
        self.lookups.append(host)
        answers = self.table[host]
        answer = answers.pop(0) if len(answers) > 1 else answers[0]
        return [ipaddress.ip_address(a) for a in answer]


def build(
    routes: Mapping[str, Route], dns: dict[str, list[list[str]]] | None = None
) -> tuple[HttpxPageFetcher, list[httpx.Request]]:
    """A fetcher whose server is ``routes`` keyed by ``host/path``; requests are logged."""
    seen: list[httpx.Request] = []

    def handle(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        key = f"{request.headers['host']}{request.url.path}"
        route = routes.get(key)
        return route(request) if route else httpx.Response(404)

    table = dns if dns is not None else {"example.org": [["93.184.215.14"]]}
    fetcher = HttpxPageFetcher(
        resolver=FakeDns(table), transport=httpx.MockTransport(handle)
    )
    return fetcher, seen


def html(body: str, status: int = 200) -> Route:
    """A route answering with an HTML page."""
    return lambda _: httpx.Response(status, html=f"<html><body>{body}</body></html>")


def redirect(location: str, status: int = 302) -> Route:
    """A route answering with a redirect."""
    return lambda _: httpx.Response(status, headers={"location": location})


ARTICLE = (
    "<article><p>" + "Sejm uchwalił ustawę o ochronie danych. " * 20 + "</p></article>"
)
"""A page whose main text trafilatura finds."""


class Web:
    """The fakes, bundled for the ``web`` fixture."""

    build = staticmethod(build)
    html = staticmethod(html)
    redirect = staticmethod(redirect)
    article = ARTICLE


@pytest.fixture
def web() -> Web:
    """In-process server, DNS and page helpers."""
    return Web()
