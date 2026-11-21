"""Page fetcher content rules: main text, walls, media types, limits, robots.txt."""

import asyncio
from collections.abc import AsyncIterator, Callable, Mapping
from typing import TYPE_CHECKING

import httpx
import pytest

from meritum_core.corpus.fetching import (
    FetchedPage,
    FetchFailureReason,
    FetchPurpose,
    JavaScriptRequiredError,
    LoginWallError,
    PageFetchError,
    RobotsDisallowedError,
    build_page_fetcher,
)
from meritum_core.corpus.fetching.constants import MAX_RESPONSE_BYTES

if TYPE_CHECKING:
    from tests.corpus.conftest import Web

URL = "https://example.org/post"

type Route = Callable[[httpx.Request], httpx.Response]
type Routes = Mapping[str, Route]


def fetch(
    web: Web, routes: Routes, purpose: FetchPurpose = FetchPurpose.USER_LINK
) -> FetchedPage:
    fetcher, _ = web.build(routes)
    return asyncio.run(fetcher.fetch(URL, purpose=purpose))


def failure(
    web: Web, routes: Routes, purpose: FetchPurpose = FetchPurpose.USER_LINK
) -> PageFetchError:
    with pytest.raises(PageFetchError) as caught:
        fetch(web, routes, purpose)
    return caught.value


def test_main_text_of_html_is_returned_as_untrusted_text(web: Web) -> None:
    page = fetch(web, {"example.org/post": web.html("<nav>Menu</nav>" + web.article)})
    assert page.untrusted_text.startswith("Sejm uchwalił ustawę")
    assert "Menu" not in page.untrusted_text
    assert (page.url, page.content_type) == (URL, "text/html")


def test_plain_text_is_returned_as_is(web: Web) -> None:
    route = {"example.org/post": lambda _: httpx.Response(200, text=" Komunikat. ")}
    assert fetch(web, route).untrusted_text == "Komunikat."


def test_html_without_main_text_needs_javascript(web: Web) -> None:
    error = failure(web, {"example.org/post": web.html('<div id="root"></div>')})
    assert isinstance(error, JavaScriptRequiredError)
    assert error.asks_for_text


@pytest.mark.parametrize("status", [401, 403, 407])
def test_status_asking_for_an_account_is_a_login_wall(web: Web, status: int) -> None:
    error = failure(web, {"example.org/post": web.html("Zaloguj się", status)})
    assert isinstance(error, LoginWallError)
    assert error.reason is FetchFailureReason.LOGIN_WALL
    assert (error.check_status, error.asks_for_text) == ("technical_failure", True)


def test_redirect_to_a_login_page_is_a_login_wall(web: Web) -> None:
    routes = {
        "example.org/post": web.redirect("/login/?next=%2Fpost"),
        "example.org/login/": web.html('<form><input type="password"></form>'),
    }
    assert failure(web, routes).reason is FetchFailureReason.LOGIN_WALL


def test_login_form_without_main_text_is_a_login_wall(web: Web) -> None:
    form = '<form><input name="email"><input type="password" name="pass"></form>'
    assert failure(web, {"example.org/post": web.html(form)}).reason == "login_wall"


def test_article_with_a_login_box_in_the_header_is_read(web: Web) -> None:
    body = '<header><input type="password"></header>' + web.article
    assert fetch(web, {"example.org/post": web.html(body)}).untrusted_text


@pytest.mark.parametrize(
    "route",
    [
        lambda web: web.html("Zapłać", 402),
        lambda web: web.html(
            '<script type="application/ld+json">{"isAccessibleForFree": false}'
            "</script>" + web.article
        ),
    ],
    ids=["status-402", "schema-org-flag"],
)
def test_paywall_is_reported_separately(
    web: Web, route: Callable[[Web], Route]
) -> None:
    error = failure(web, {"example.org/post": route(web)})
    assert isinstance(error, LoginWallError)
    assert error.reason is FetchFailureReason.PAYWALL


@pytest.mark.parametrize("status", [404, 500, 503])
def test_error_status_is_an_http_error(web: Web, status: int) -> None:
    error = failure(web, {"example.org/post": web.html(web.article, status)})
    assert error.reason is FetchFailureReason.HTTP_ERROR
    assert not error.asks_for_text


@pytest.mark.parametrize("media", ["application/pdf", "image/png", "application/json"])
def test_unsupported_media_type_is_not_read(web: Web, media: str) -> None:
    route = {
        "example.org/post": lambda _: httpx.Response(
            200, content=b"x", headers={"content-type": media}
        )
    }
    assert failure(web, route).reason is FetchFailureReason.UNSUPPORTED_CONTENT


def test_declared_oversized_body_is_refused(web: Web) -> None:
    big = b"a" * (MAX_RESPONSE_BYTES + 1)
    route = {
        "example.org/post": lambda _: httpx.Response(
            200, content=big, headers={"content-type": "text/plain"}
        )
    }
    assert failure(web, route).reason is FetchFailureReason.TOO_LARGE


def test_streamed_oversized_body_is_cut(web: Web) -> None:
    async def chunks() -> AsyncIterator[bytes]:  # ruff: ignore[unused-async]  # httpx wants an async stream
        for _ in range(6):
            yield b"a" * (1024 * 1024)

    route = {
        "example.org/post": lambda _: httpx.Response(
            200, content=chunks(), headers={"content-type": "text/plain"}
        )
    }
    assert failure(web, route).reason is FetchFailureReason.TOO_LARGE


def test_timeout_is_reported_without_details(web: Web) -> None:
    def slow(request: httpx.Request) -> httpx.Response:
        detail = "read from 93.184.215.14 timed out"
        raise httpx.ReadTimeout(detail, request=request)

    error = failure(web, {"example.org/post": slow})
    assert (error.reason, str(error)) == (FetchFailureReason.TIMEOUT, "timeout")


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
        assert fetch(web, routes, FetchPurpose.SOURCE).untrusted_text
    else:
        assert isinstance(
            failure(web, routes, FetchPurpose.SOURCE), RobotsDisallowedError
        )


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
    assert fetch(web, routes).untrusted_text


def test_factory_builds_a_fetcher_that_refuses_internal_addresses() -> None:
    fetcher = build_page_fetcher()
    with pytest.raises(PageFetchError) as caught:
        asyncio.run(fetcher.fetch("http://127.0.0.1/", purpose=FetchPurpose.USER_LINK))
    assert caught.value.reason is FetchFailureReason.BLOCKED_ADDRESS
