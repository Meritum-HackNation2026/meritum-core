"""Sources honour robots.txt and its Content-Signal; a pasted link does not."""

import asyncio
from collections.abc import Callable
from typing import TYPE_CHECKING

import httpx
import pytest

from meritum_core.corpus.fetching import (
    FetchPurpose,
    RobotsDisallowedError,
    signal_denies,
)

if TYPE_CHECKING:
    from tests.corpus.conftest import Web

URL = "https://example.org/post"

type Route = Callable[[httpx.Request], httpx.Response]


def fetch(web: Web, routes: dict[str, Route], purpose: FetchPurpose) -> str:
    fetcher, _ = web.build(routes)
    return asyncio.run(fetcher.fetch(URL, purpose=purpose)).untrusted_text


def robots(text: str, status: int = 200) -> Route:
    return lambda _: httpx.Response(status, text=text)


@pytest.mark.parametrize(
    ("robots_route", "allowed"),
    [
        (robots("User-agent: *\nDisallow: /post"), False),
        (
            robots("User-agent: MeritumBot\nDisallow: /\n\nUser-agent: *\nAllow: /"),
            False,
        ),
        (robots("User-agent: OtherBot\nDisallow: /\n"), True),
        (
            robots("User-agent: *\nContent-Signal: search=yes, ai-input=no\nAllow: /"),
            False,
        ),
        (robots("User-agent: *\nContent-Signal: ai-train=no, ai-input=yes\n"), True),
        (robots("User-agent: OtherBot\nContent-Signal: ai-input=no\n"), True),
        (robots("", 404), True),
        (
            lambda _: httpx.Response(200, content=b"User-agent: *\nDisallow: /"),
            False,
        ),
        (robots("", 503), False),
    ],
    ids=[
        "disallow",
        "own-group",
        "other-bot",
        "signal-no",
        "signal-yes",
        "signal-other-bot",
        "missing",
        "no-content-type",
        "server-error",
    ],
)
def test_sources_honour_robots_txt_and_content_signal(
    web: Web,
    robots_route: Route,
    allowed: bool,  # ruff: ignore[boolean-type-hint-positional-argument]  # parametrized
) -> None:
    routes = {
        "example.org/robots.txt": robots_route,
        "example.org/post": web.html(web.article),
    }
    if allowed:
        assert fetch(web, routes, FetchPurpose.SOURCE)
    else:
        with pytest.raises(RobotsDisallowedError):
            fetch(web, routes, FetchPurpose.SOURCE)


def test_robots_txt_of_every_host_on_the_redirect_path_is_honoured(web: Web) -> None:
    routes = {
        "example.org/robots.txt": robots("User-agent: *\nAllow: /"),
        "example.org/post": web.redirect("https://mirror.example/post"),
        "mirror.example/robots.txt": robots("User-agent: *\nDisallow: /"),
        "mirror.example/post": web.html(web.article),
    }
    dns = {"example.org": [["93.184.215.14"]], "mirror.example": [["93.184.215.15"]]}
    fetcher, seen = web.build(routes, dns)
    with pytest.raises(RobotsDisallowedError):
        asyncio.run(fetcher.fetch(URL, purpose=FetchPurpose.SOURCE))
    assert "mirror.example/post" not in [r.headers["host"] + r.url.path for r in seen]


def test_a_pasted_link_is_fetched_on_the_citizens_behalf_without_robots(
    web: Web,
) -> None:
    routes = {
        "example.org/robots.txt": robots("User-agent: *\nDisallow: /"),
        "example.org/post": web.html(web.article),
    }
    assert fetch(web, routes, FetchPurpose.USER_LINK)


@pytest.mark.parametrize(
    ("signal", "denies"),
    [
        ("search=yes, AI-Train=NO", True),
        ("ai-train=yes, ai-input=no", True),
        ("search=no", False),
        ("ai-train", False),
    ],
)
def test_signal_denies_a_use_answered_no(
    signal: str,
    denies: bool,  # ruff: ignore[boolean-type-hint-positional-argument]  # parametrized
) -> None:
    assert signal_denies(signal, {"ai-train", "ai-input"}) is denies
