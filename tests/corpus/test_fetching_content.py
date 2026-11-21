"""Page fetcher content rules: main text, walls, media types and limits."""

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
    PaywallError,
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


def test_article_under_a_login_like_path_is_read_when_not_redirected(web: Web) -> None:
    fetcher, _ = web.build({"example.org/auth/post": web.html(web.article)})
    url = "https://example.org/auth/post"
    page = asyncio.run(fetcher.fetch(url, purpose=FetchPurpose.USER_LINK))
    assert page.untrusted_text


def test_unknown_charset_falls_back_to_utf8(web: Web) -> None:
    body = f"<html><body>{web.article}</body></html>".encode()
    headers = {"content-type": "text/html; charset=bogus"}
    route = {
        "example.org/post": lambda _: httpx.Response(200, content=body, headers=headers)
    }
    assert fetch(web, route).untrusted_text.startswith("Sejm uchwalił")


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
    assert isinstance(error, PaywallError)
    assert error.reason is FetchFailureReason.PAYWALL


@pytest.mark.parametrize("status", [500, 503])
def test_error_status_is_an_http_error(web: Web, status: int) -> None:
    error = failure(web, {"example.org/post": web.html(web.article, status)})
    assert error.reason is FetchFailureReason.HTTP_ERROR
    assert not error.asks_for_text


@pytest.mark.parametrize("status", [404, 410])
def test_missing_page_is_not_found(web: Web, status: int) -> None:
    error = failure(web, {"example.org/post": web.html(web.article, status)})
    assert error.reason is FetchFailureReason.NOT_FOUND


@pytest.mark.parametrize(
    ("meta", "reserved"),
    [
        ('<meta name="tdm-reservation" content="1">', True),
        ('<meta name="TDM-Reservation" content="0">', False),
        ('<meta name="robots" content="index, NoAI">', True),
        ('<meta name="robots" content="noindex">', False),
        ("", False),
    ],
)
def test_meta_tags_tell_whether_mining_is_reserved(
    web: Web, meta: str, *, reserved: bool
) -> None:
    html = f"<html><head>{meta}</head><body>{web.article}</body></html>"
    route = {"example.org/post": lambda _: httpx.Response(200, html=html)}
    assert fetch(web, route).tdm_reserved is reserved


@pytest.mark.parametrize("media", ["application/pdf", "image/png", "application/json"])
def test_unsupported_media_type_is_not_read(web: Web, media: str) -> None:
    route = {
        "example.org/post": lambda _: httpx.Response(
            200, content=b"x", headers={"content-type": media}
        )
    }
    assert failure(web, route).reason is FetchFailureReason.UNSUPPORTED_CONTENT


def test_large_unsupported_file_is_refused_by_type_without_reading(web: Web) -> None:
    pdf = b"%PDF" * (MAX_RESPONSE_BYTES // 4 + 1)
    headers = {"content-type": "application/pdf"}
    route = {
        "example.org/post": lambda _: httpx.Response(200, content=pdf, headers=headers)
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


def test_factory_builds_a_fetcher_that_refuses_internal_addresses() -> None:
    fetcher = build_page_fetcher()
    with pytest.raises(PageFetchError) as caught:
        asyncio.run(fetcher.fetch("http://127.0.0.1/", purpose=FetchPurpose.USER_LINK))
    assert caught.value.reason is FetchFailureReason.BLOCKED_ADDRESS
