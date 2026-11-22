"""Page fetcher for pages that need JavaScript: a local Crawl4AI renders them.

Crawl4AI is a separate HTTP service with its own browser, so it cannot use our
pinned connection. The guards around it: it is called only after the httpx
fetcher passed every check (URL, public address on every hop, robots.txt and
Content-Signal) and found no main text; the address is resolved and checked
again right before the render; a render that lands on another host or on an
internal address is discarded. Subresources the browser loads are stopped by
the container's network, not here (README, ``deploy/crawl4ai``).

Features:
    US-SPR-07, US-KOR-03, F-06, ADR-32
"""

import asyncio
from typing import Any

import httpx

from meritum_core.corpus.fetching.adapters._extract import RawResponse, to_page
from meritum_core.corpus.fetching.adapters._guard import checked_url, pinned_address
from meritum_core.corpus.fetching.constants import (
    CRAWL4AI_CRAWL_PATH,
    CRAWL4AI_MAX_REPLY_BYTES,
    CRAWL4AI_TIMEOUT_S,
    MAX_RESPONSE_BYTES,
)
from meritum_core.corpus.fetching.errors import (
    BlockedAddressError,
    JavaScriptRequiredError,
    PageFetchError,
)
from meritum_core.corpus.fetching.models import (
    FetchedPage,
    FetchFailureReason,
    FetchPurpose,
)
from meritum_core.corpus.fetching.ports import PageFetcherPort, Resolver


def _crawl_request(url: str) -> dict[str, Any]:
    return {
        "urls": [url],
        "browser_config": {"type": "BrowserConfig", "params": {"headless": True}},
        "crawler_config": {
            "type": "CrawlerRunConfig",
            "params": {"stream": False, "cache_mode": "bypass"},
        },
    }


def _first_result(reply: httpx.Response) -> dict[str, Any]:
    if not reply.is_success or len(reply.content) > CRAWL4AI_MAX_REPLY_BYTES:
        raise PageFetchError(FetchFailureReason.UNREACHABLE)
    try:
        result = reply.json()["results"][0]
    except ValueError, KeyError, IndexError, TypeError:
        raise PageFetchError(FetchFailureReason.UNREACHABLE) from None
    if not isinstance(result, dict) or not result.get("success"):
        raise PageFetchError(FetchFailureReason.UNREACHABLE)
    return result


class Crawl4AiPageFetcher:
    """Fetches with ``first``; renders through Crawl4AI only on ``javascript_required``.

    Args:
        first: the SSRF-safe httpx fetcher; its checks run before any render.
        endpoint: base URL of the Crawl4AI service.
        token: Crawl4AI's API token.
        resolver: the DNS resolver for the re-checks.
        transport: the httpx transport to Crawl4AI (tests replay recorded replies).

    Features:
        US-SPR-07, US-KOR-03, F-06, ADR-32
    """

    def __init__(
        self,
        first: PageFetcherPort,
        *,
        endpoint: str,
        token: str,
        resolver: Resolver,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self._first = first
        self._crawl_url = endpoint.rstrip("/") + CRAWL4AI_CRAWL_PATH
        self._token = token
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
            US-SPR-07, US-KOR-03, F-06, ADR-32
        """
        try:
            return await self._first.fetch(url, purpose=purpose)
        except JavaScriptRequiredError:
            pass  # every guard of the first fetch passed; only the text is missing
        target = checked_url(url)
        await pinned_address(target, self._resolver, redirected=False)
        result = await self._render(str(target))
        final = await self._checked_final(target, result.get("redirected_url") or url)
        html = str(result.get("html") or "")
        if len(html.encode()) > MAX_RESPONSE_BYTES:
            raise PageFetchError(FetchFailureReason.TOO_LARGE)
        status = result.get("status_code")
        response = RawResponse(
            str(final),
            status if isinstance(status, int) else 200,
            "text/html",
            html,
            redirected=final != target,
        )
        return await asyncio.to_thread(to_page, response)

    async def _checked_final(self, target: httpx.URL, final: str) -> httpx.URL:
        try:
            landed = checked_url(final)
        except PageFetchError:
            raise BlockedAddressError(FetchFailureReason.REDIRECT_BLOCKED) from None
        if landed.netloc != target.netloc:
            # shortcut: another host would need its own robots.txt check; refuse it
            raise BlockedAddressError(FetchFailureReason.REDIRECT_BLOCKED)
        await pinned_address(landed, self._resolver, redirected=True)
        return landed

    async def _render(self, url: str) -> dict[str, Any]:
        try:
            async with httpx.AsyncClient(
                transport=self._transport,
                timeout=httpx.Timeout(CRAWL4AI_TIMEOUT_S),
                follow_redirects=False,
                trust_env=False,
                headers={"authorization": f"Bearer {self._token}"},
            ) as client:
                reply = await client.post(self._crawl_url, json=_crawl_request(url))
        except httpx.TimeoutException:
            raise PageFetchError(FetchFailureReason.TIMEOUT) from None
        except httpx.HTTPError:
            raise PageFetchError(FetchFailureReason.UNREACHABLE) from None
        return _first_result(reply)
