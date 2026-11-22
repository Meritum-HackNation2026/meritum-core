"""Steps for the page-fetching scenarios of features/checks.feature.

The server is an in-process httpx handler and DNS a table: no network.
"""

import asyncio
import ipaddress
from datetime import date

import httpx
from behave import given, then, when
from behave.runner import Context

from meritum_core.corpus.fetching import (
    BlockedAddressError,
    FetchFailureReason,
    FetchPurpose,
    PageFetchError,
    build_page_fetcher,
)

type Address = ipaddress.IPv4Address | ipaddress.IPv6Address

PUBLIC = {"news.example": "93.184.215.14", "www.facebook.com": "157.240.1.35"}


def _serve(context: Context, pages: dict[str, httpx.Response]) -> None:
    context.requests = []

    def handle(request: httpx.Request) -> httpx.Response:
        context.requests.append(request)
        return pages.get(
            request.headers["host"] + request.url.path, httpx.Response(404)
        )

    async def resolve(host: str) -> list[Address]:  # ruff: ignore[unused-async]  # Resolver is async
        return [ipaddress.ip_address(PUBLIC[host])]

    context.fetcher = build_page_fetcher(
        resolver=resolve, transport=httpx.MockTransport(handle)
    )


@given('link "{url}"')
def given_link(context: Context, url: str) -> None:
    """A citizen pasted ``url``; the server answers nothing."""
    _serve(context, {})
    context.url = url


@given('publiczny adres, który przekierowuje na "{location}"')
def given_redirect(context: Context, location: str) -> None:
    """A public page that redirects to ``location``."""
    _serve(
        context, {"news.example/a": httpx.Response(302, headers={"location": location})}
    )
    context.url = "https://news.example/a"


@given("link do posta na Facebooku wymagającego logowania")
def given_facebook_post(context: Context) -> None:
    """Facebook sends a logged-out visitor to its login page."""
    login = "https://www.facebook.com/login/?next=%2Fpost%2F1"
    _serve(
        context,
        {
            "www.facebook.com/post/1": httpx.Response(302, headers={"location": login}),
            "www.facebook.com/login/": httpx.Response(
                200, html='<input type="password">'
            ),
        },
    )
    context.url = "https://www.facebook.com/post/1"


BOT_BLOCK_PAGES = {
    "Incapsula z kodem 200": httpx.Response(
        200,
        html="<html><body>Request unsuccessful. Incapsula incident ID: "
        "1234-5678</body></html>",
    ),
    "AWS WAF z kodem 202": httpx.Response(
        202, html='<html><body><script src="challenge.js"></script></body></html>'
    ),
}


@given("serwis za ochroną antybotową odpowiada stroną blokady {provider}")
def given_bot_block_page(context: Context, provider: str) -> None:
    """A public office site whose anti-bot layer answers with its block page."""
    _serve(context, {"news.example/a": BOT_BLOCK_PAGES[provider]})
    context.url = "https://news.example/a"


ARTICLE = "<p>" + "Sejm uchwalił ustawę o ochronie danych. " * 20 + "</p>"


@given("publiczna strona HTML z datą publikacji {day} w metadanych")
def given_page_with_date(context: Context, day: str) -> None:
    """An article whose head carries ``article:published_time``."""
    meta = f'<meta property="article:published_time" content="{day}T09:30:00+01:00">'
    html = f"<html><head>{meta}</head><body><article>{ARTICLE}</article></body></html>"
    _serve(context, {"news.example/a": httpx.Response(200, html=html)})
    context.url = "https://news.example/a"


@given("publiczna strona HTML bez daty w metadanych")
def given_page_without_date(context: Context) -> None:
    """An article with no date anywhere in its markup."""
    html = f"<html><body><article>{ARTICLE}</article></body></html>"
    _serve(context, {"news.example/a": httpx.Response(200, html=html)})
    context.url = "https://news.example/a"


@when("fetcher pobiera ją jako link użytkownika")
@when("fetcher ją pobiera")
def when_fetching_page(context: Context) -> None:
    """Fetch the link and keep the page."""
    fetch = context.fetcher.fetch(context.url, purpose=FetchPurpose.USER_LINK)
    context.page = asyncio.run(fetch)


@then("FetchedPage ma published_at {day}")
def then_published_at(context: Context, day: str) -> None:
    """The page's publication date is ``day`` (``None`` for no date)."""
    expected = None if day == "None" else date.fromisoformat(day)
    assert context.page.published_at == expected


@when("system próbuje pobrać stronę")
@when("system pobiera stronę")
def when_fetching(context: Context) -> None:
    """Fetch the link and keep the error."""
    try:
        asyncio.run(context.fetcher.fetch(context.url, purpose=FetchPurpose.USER_LINK))
    except PageFetchError as error:
        context.error = error
    else:
        context.error = None


@then("pobranie jest zablokowane przed połączeniem")
def then_blocked_before_connecting(context: Context) -> None:
    """Nothing reached the server."""
    assert isinstance(context.error, BlockedAddressError)
    assert context.requests == []


@then('wynik to "{status}" bez szczegółów sieci w komunikacie')
def then_failure_without_details(context: Context, status: str) -> None:
    """The message is the reason code, never the address."""
    assert context.error.check_status == status
    assert str(context.error) == FetchFailureReason.BLOCKED_ADDRESS
    assert "169.254" not in str(context.error)


@then("przekierowanie jest zablokowane")
def then_redirect_blocked(context: Context) -> None:
    """The first hop was fetched, the redirect target never."""
    assert context.error.reason is FetchFailureReason.REDIRECT_BLOCKED
    assert [r.headers["host"] for r in context.requests] == ["news.example"]


@then('wynik to "{status}" z prośbą o wklejenie tekstu')
def then_failure_asks_for_text(context: Context, status: str) -> None:
    """A login wall asks the citizen to paste the text."""
    assert context.error.check_status == status
    assert context.error.reason is FetchFailureReason.LOGIN_WALL
    assert context.error.asks_for_text


@then('wynik to "{status}" z powodem "{reason}"')
def then_failure_with_reason(context: Context, status: str, reason: str) -> None:
    """The fetch failed with ``reason`` instead of returning the page."""
    assert context.error is not None
    assert context.error.check_status == status
    assert context.error.reason == reason
