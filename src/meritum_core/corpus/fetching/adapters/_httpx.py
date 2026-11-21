"""Page fetcher on httpx: every hop pinned to a checked public address.

Features:
    US-SPR-07, F-06
"""

import asyncio
import codecs
import dataclasses
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import httpx

from meritum_core.corpus.fetching.adapters._extract import RawResponse, to_page
from meritum_core.corpus.fetching.adapters._guard import (
    checked_url,
    pinned_address,
    system_resolver,
)
from meritum_core.corpus.fetching.adapters._robots import robots_allow
from meritum_core.corpus.fetching.constants import (
    ALLOWED_CONTENT_TYPES,
    CONNECT_TIMEOUT_S,
    DEFAULT_CHARSET,
    FETCH_TIMEOUT_S,
    MAX_REDIRECTS,
    MAX_RESPONSE_BYTES,
    REDIRECT_STATUSES,
    ROBOTS_PATH,
    USER_AGENT,
)
from meritum_core.corpus.fetching.errors import PageFetchError, RobotsDisallowedError
from meritum_core.corpus.fetching.models import (
    FetchedPage,
    FetchFailureReason,
    FetchPurpose,
)
from meritum_core.corpus.fetching.ports import Resolver


async def _read_limited(response: httpx.Response) -> str:
    declared = _header(response, "content-length")
    if declared.isdigit() and int(declared) > MAX_RESPONSE_BYTES:
        raise PageFetchError(FetchFailureReason.TOO_LARGE)
    body = bytearray()
    async for chunk in response.aiter_bytes():
        body += chunk
        if len(body) > MAX_RESPONSE_BYTES:
            raise PageFetchError(FetchFailureReason.TOO_LARGE)
    return body.decode(_charset(response), errors="replace")


def _charset(response: httpx.Response) -> str:
    declared = response.charset_encoding or DEFAULT_CHARSET
    try:
        return codecs.lookup(declared).name
    except LookupError:  # the server named an encoding Python does not know
        return DEFAULT_CHARSET


def _header(response: httpx.Response, name: str) -> str:
    return str(response.headers.get(name, ""))  # httpx types Headers.get as Any


def _media_type(response: httpx.Response) -> str:
    media = _header(response, "content-type").split(";", maxsplit=1)[0]
    return media.strip().lower()


class HttpxPageFetcher:
    """SSRF-safe fetcher: http(s) only, public addresses only, bounded.

    Each hop resolves the host once, refuses internal addresses, then connects to
    that very address with the original Host header and TLS SNI, so DNS
    rebinding cannot redirect the connection. Redirects are followed by hand.

    Args:
        resolver: the DNS resolver (tests substitute one).
        transport: the httpx transport (tests run an in-process server).

    Features:
        US-SPR-07, F-06
    """

    def __init__(
        self,
        *,
        resolver: Resolver = system_resolver,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self._resolver = resolver
        self._transport = transport

    async def fetch(self, url: str, *, purpose: FetchPurpose) -> FetchedPage:
        """Fetch one page; see ``PageFetcherPort.fetch``.

        Args:
            url: an absolute http(s) URL.
            purpose: ``SOURCE`` also honours robots.txt and Content-Signal.

        Returns:
            The page's main text, marked as untrusted data.

        Raises:
            PageFetchError: The page could not be fetched; ``reason`` says why.

        Features:
            US-SPR-07, F-06
        """
        target = checked_url(url)
        try:
            async with asyncio.timeout(FETCH_TIMEOUT_S), self._client() as client:
                honour_robots = purpose is FetchPurpose.SOURCE
                response = await self._follow(client, target, robots=honour_robots)
                # trafilatura is CPU-bound: off the event loop, inside the budget.
                # shortcut: after a timeout the thread still finishes in the default
                # executor; give extraction its own small pool if pages pile up.
                return await asyncio.to_thread(to_page, response)
        except TimeoutError, httpx.TimeoutException:
            raise PageFetchError(FetchFailureReason.TIMEOUT) from None
        except httpx.HTTPError:
            raise PageFetchError(FetchFailureReason.UNREACHABLE) from None

    @asynccontextmanager
    async def _client(self) -> AsyncGenerator[httpx.AsyncClient]:
        async with httpx.AsyncClient(
            transport=self._transport,
            timeout=httpx.Timeout(CONNECT_TIMEOUT_S),
            follow_redirects=False,
            trust_env=False,  # an env proxy would connect by host name, unpinned
            headers={"user-agent": USER_AGENT},
        ) as client:
            yield client

    async def _check_robots(self, client: httpx.AsyncClient, url: httpx.URL) -> None:
        robots = url.copy_with(path=ROBOTS_PATH, query=None, fragment=None)
        response = await self._follow(client, robots, robots=False)
        if response.is_client_error:  # RFC 9309: no robots.txt, all allowed
            return
        if not response.is_success or not robots_allow(response.text, str(url)):
            raise RobotsDisallowedError

    async def _follow(
        self, client: httpx.AsyncClient, url: httpx.URL, *, robots: bool
    ) -> RawResponse:
        checked_hosts: set[bytes] = set()
        for hop in range(MAX_REDIRECTS + 1):
            if robots and url.netloc not in checked_hosts:
                await self._check_robots(client, url)  # every host on the path
                checked_hosts.add(url.netloc)
            response = await self._get(client, url, redirected=hop > 0)
            if not response.location:
                return dataclasses.replace(response, redirected=hop > 0)
            url = checked_url(url.join(response.location))
        raise PageFetchError(FetchFailureReason.TOO_MANY_REDIRECTS)

    async def _get(
        self, client: httpx.AsyncClient, url: httpx.URL, *, redirected: bool
    ) -> RawResponse:
        address = await pinned_address(url, self._resolver, redirected=redirected)
        request = client.build_request(
            "GET",
            url.copy_with(host=str(address)),
            headers={"host": url.netloc.decode("ascii")},
            extensions={"sni_hostname": url.host},
        )
        response = await client.send(request, stream=True)
        try:
            return await self._read(response, url)
        finally:
            await response.aclose()

    @staticmethod
    async def _read(response: httpx.Response, url: httpx.URL) -> RawResponse:
        location = _header(response, "location")
        if response.status_code in REDIRECT_STATUSES and location:
            return RawResponse(str(url), response.status_code, location=location)
        media = _media_type(response)
        # robots.txt is read whatever its media type (RFC 9309 asks for none)
        is_readable = media in ALLOWED_CONTENT_TYPES or url.path == ROBOTS_PATH
        text = (
            await _read_limited(response) if response.is_success and is_readable else ""
        )
        return RawResponse(str(url), response.status_code, media, text)
