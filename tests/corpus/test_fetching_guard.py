"""SSRF guard of the page fetcher: schemes, private addresses, redirects, DNS."""

import asyncio
from typing import TYPE_CHECKING

import httpx
import pytest

from meritum_core.corpus.fetching import (
    BlockedAddressError,
    FetchedPage,
    FetchFailureReason,
    FetchPurpose,
    PageFetcherPort,
    PageFetchError,
)

if TYPE_CHECKING:
    from tests.corpus.conftest import Web

BLOCKED = [
    "127.0.0.1",
    "10.0.0.5",
    "172.16.0.1",
    "192.168.1.1",
    "169.254.169.254",
    "100.64.0.1",
    "0.0.0.0",  # ruff: ignore[hardcoded-bind-all-interfaces]  # the address under test, not a bind
    "224.0.0.1",
    "233.252.0.1",
    "::1",
    "fe80::1",
    "fc00::1",
    "ff02::1",
    "::ffff:127.0.0.1",
    "64:ff9b::a00:5",
    "2002:7f00:1::",
    "::ffff:0:a00:5",
    "::a00:5",
    "fec0::1",
]


def fetch(fetcher: PageFetcherPort, url: str) -> FetchedPage:
    return asyncio.run(fetcher.fetch(url, purpose=FetchPurpose.USER_LINK))


@pytest.mark.parametrize("address", BLOCKED)
def test_literal_internal_address_is_blocked_before_connecting(
    web: Web, address: str
) -> None:
    fetcher, seen = web.build({})
    host = f"[{address}]" if ":" in address else address
    with pytest.raises(BlockedAddressError) as caught:
        fetch(fetcher, f"http://{host}/latest/meta-data/")
    assert seen == []
    assert caught.value.check_status == "technical_failure"
    assert address not in str(caught.value)


@pytest.mark.parametrize("address", BLOCKED)
def test_hostname_resolving_to_internal_address_is_blocked(
    web: Web, address: str
) -> None:
    fetcher, seen = web.build({}, {"intranet.example": [[address]]})
    with pytest.raises(BlockedAddressError):
        fetch(fetcher, "https://intranet.example/")
    assert seen == []


def test_any_internal_record_among_public_ones_blocks_the_host(web: Web) -> None:
    fetcher, seen = web.build({}, {"mixed.example": [["93.184.215.14", "10.0.0.5"]]})
    with pytest.raises(BlockedAddressError):
        fetch(fetcher, "https://mixed.example/")
    assert seen == []


@pytest.mark.parametrize(
    "url",
    [
        "file:///etc/passwd",
        "ftp://example.org/x",
        "gopher://example.org/",
        "javascript:alert(1)",
        "http://user:secret@example.org/",
        "http:///nohost",
        "not a url",
    ],
)
def test_only_plain_http_and_https_urls_are_accepted(web: Web, url: str) -> None:
    fetcher, seen = web.build({})
    with pytest.raises(PageFetchError) as caught:
        fetch(fetcher, url)
    assert caught.value.reason is FetchFailureReason.UNSUPPORTED_URL
    assert seen == []


@pytest.mark.parametrize(
    "location",
    ["http://10.0.0.5/", "http://[::1]/", "http://localhost.example/"],
)
def test_redirect_to_internal_address_is_blocked(web: Web, location: str) -> None:
    routes = {"example.org/": web.redirect(location)}
    dns = {"example.org": [["93.184.215.14"]], "localhost.example": [["127.0.0.1"]]}
    fetcher, seen = web.build(routes, dns)
    with pytest.raises(BlockedAddressError) as caught:
        fetch(fetcher, "http://example.org/")
    assert caught.value.reason is FetchFailureReason.REDIRECT_BLOCKED
    assert len(seen) == 1


def test_redirect_to_another_scheme_is_refused(web: Web) -> None:
    fetcher, _ = web.build({"example.org/": web.redirect("file:///etc/passwd")})
    with pytest.raises(PageFetchError) as caught:
        fetch(fetcher, "http://example.org/")
    assert caught.value.reason is FetchFailureReason.UNSUPPORTED_URL


def test_redirect_chain_is_limited(web: Web) -> None:
    routes = {f"example.org/{i}": web.redirect(f"/{i + 1}") for i in range(20)}
    fetcher, seen = web.build(routes)
    with pytest.raises(PageFetchError) as caught:
        fetch(fetcher, "http://example.org/0")
    assert caught.value.reason is FetchFailureReason.TOO_MANY_REDIRECTS
    assert len(seen) == 6


def test_public_redirect_is_followed_relative_to_the_original_host(web: Web) -> None:
    routes = {
        "example.org/old": web.redirect("/new", 301),
        "example.org/new": web.html(web.article),
    }
    fetcher, _ = web.build(routes)
    page = fetch(fetcher, "http://example.org/old")
    assert page.url == "http://example.org/new"


def test_connection_goes_to_the_checked_address_with_original_host_and_sni(
    web: Web,
) -> None:
    fetcher, seen = web.build({"example.org/": web.html(web.article)})
    fetch(fetcher, "https://example.org/")
    (request,) = seen
    assert request.url.host == "93.184.215.14"
    assert request.headers["host"] == "example.org"
    assert request.extensions["sni_hostname"] == "example.org"


def test_dns_rebinding_cannot_swap_the_address_after_the_check(web: Web) -> None:
    dns = {"rebind.example": [["93.184.215.14"], ["127.0.0.1"]]}
    fetcher, seen = web.build({"rebind.example/": web.html(web.article)}, dns)
    fetch(fetcher, "http://rebind.example/")
    assert [r.url.host for r in seen] == ["93.184.215.14"]


def test_ipv6_public_address_is_reached_in_brackets(web: Web) -> None:
    dns = {"v6.example": [["2606:2800:21f:cb07:6820:80da:af6b:8b2c"]]}
    fetcher, seen = web.build({"v6.example/": web.html(web.article)}, dns)
    fetch(fetcher, "http://v6.example/")
    assert str(seen[0].url).startswith(
        "http://[2606:2800:21f:cb07:6820:80da:af6b:8b2c]/"
    )


def test_network_failure_has_no_network_details(web: Web) -> None:
    def refuse(request: httpx.Request) -> httpx.Response:
        detail = "connect to 93.184.215.14 refused"
        raise httpx.ConnectError(detail, request=request)

    fetcher, _ = web.build({"example.org/": refuse})
    with pytest.raises(PageFetchError) as caught:
        fetch(fetcher, "http://example.org/")
    assert caught.value.reason is FetchFailureReason.UNREACHABLE
    assert "93.184" not in str(caught.value)
    assert caught.value.__cause__ is None
