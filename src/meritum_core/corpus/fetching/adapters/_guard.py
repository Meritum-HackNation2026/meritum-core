"""SSRF guard: URL shape, DNS resolution and the public-address rule.

Features:
    US-SPR-07, F-06
"""

import asyncio
import ipaddress
import socket

import httpx

from meritum_core.corpus.fetching.constants import (
    ALLOWED_SCHEMES,
    IPV4_BITS,
    IPV4_EMBEDDING_PREFIXES,
)
from meritum_core.corpus.fetching.errors import BlockedAddressError, PageFetchError
from meritum_core.corpus.fetching.models import FetchFailureReason
from meritum_core.corpus.fetching.ports import IpAddress, Resolver


async def system_resolver(host: str) -> list[IpAddress]:
    """Resolve ``host`` with the system resolver (every A and AAAA record).

    Args:
        host: a host name or an IP literal.

    Returns:
        The addresses, in resolver order.

    Raises:
        OSError: The name does not resolve (``socket.gaierror``).

    Features:
        US-SPR-07, F-06
    """  # ruff: ignore[docstring-extraneous-exception]  # raised by the helpers it calls
    loop = asyncio.get_running_loop()
    infos = await loop.getaddrinfo(host, None, type=socket.SOCK_STREAM)
    return [ipaddress.ip_address(info[4][0]) for info in infos]


def checked_url(url: str | httpx.URL) -> httpx.URL:
    """Parse ``url`` and accept only http(s) with a host and no credentials.

    Args:
        url: the URL as given, or a redirect target already joined.

    Returns:
        The parsed URL.

    Raises:
        PageFetchError: ``unsupported_url`` for anything else.

    Features:
        US-SPR-07, F-06
    """
    try:
        parsed = httpx.URL(url)
    except httpx.InvalidURL:
        raise PageFetchError(FetchFailureReason.UNSUPPORTED_URL) from None
    has_credentials = bool(parsed.userinfo)
    if parsed.scheme not in ALLOWED_SCHEMES or not parsed.host or has_credentials:
        raise PageFetchError(FetchFailureReason.UNSUPPORTED_URL)
    return parsed


def _embedded_ipv4(address: IpAddress) -> ipaddress.IPv4Address | None:
    if isinstance(address, ipaddress.IPv4Address):
        return None
    if any(address in prefix for prefix in IPV4_EMBEDDING_PREFIXES):
        return ipaddress.IPv4Address(int(address) & IPV4_BITS)
    return address.ipv4_mapped or address.sixtofour


def _literal(host: str) -> list[IpAddress]:
    try:
        return [ipaddress.ip_address(host)]
    except ValueError:
        return []


def is_public(address: IpAddress) -> bool:
    """Whether ``address`` is globally routable unicast, embedded IPv4 included.

    Private, loopback, link-local, site-local, shared (CGNAT), reserved and
    multicast addresses, and IPv6 forms that embed them (mapped, translated,
    compatible, 6to4, NAT64), are not.

    Args:
        address: one resolved address.

    Returns:
        True when the fetcher may connect to it.

    Features:
        US-SPR-07, F-06
    """
    embedded = _embedded_ipv4(address)
    if embedded is not None and not is_public(embedded):
        return False
    is_site_local = isinstance(address, ipaddress.IPv6Address) and (
        address.is_site_local
    )
    return address.is_global and not (address.is_multicast or is_site_local)


async def pinned_address(
    url: httpx.URL, resolver: Resolver, *, redirected: bool
) -> IpAddress:
    """Resolve the URL's host once and return the address to connect to.

    Every resolved address must be public; the caller connects to the returned
    one, so a second, rebinding DNS answer is never used.

    Args:
        url: a URL that passed ``checked_url``.
        resolver: the DNS resolver.
        redirected: whether the URL came from a redirect (changes the reason).

    Returns:
        The first resolved address.

    Raises:
        BlockedAddressError: An address is internal.
        PageFetchError: ``unreachable`` when the host does not resolve.

    Features:
        US-SPR-07, F-06
    """
    try:
        addresses = _literal(url.host) or await resolver(url.host)
    except OSError:
        raise PageFetchError(FetchFailureReason.UNREACHABLE) from None
    if not addresses or not all(map(is_public, addresses)):
        reason = FetchFailureReason.REDIRECT_BLOCKED
        raise BlockedAddressError(
            reason if redirected else FetchFailureReason.BLOCKED_ADDRESS
        )
    return addresses[0]
