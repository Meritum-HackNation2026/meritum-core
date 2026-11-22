"""Limits and markers of the page fetcher, each one documented.

Features:
    US-SPR-07, F-06
"""

import ipaddress
import re
from typing import Final

from meritum_core.corpus.fetching.models import FetchFailureReason

ALLOWED_SCHEMES: Final = frozenset({"http", "https"})
"""Only plain web pages; file, ftp, gopher and the rest are refused (SSRF)."""

MAX_REDIRECTS: Final = 5
"""Redirects followed per fetch; every hop is checked like the first URL."""

FETCH_TIMEOUT_S: Final = 20.0
"""Wall-clock budget of one fetch, robots.txt and redirects included."""

CONNECT_TIMEOUT_S: Final = 5.0
"""Budget of one connection and of each read between response chunks."""

MAX_RESPONSE_BYTES: Final = 5 * 1024 * 1024
"""Largest body read; a bigger page fails with ``too_large``, memory stays bounded."""

DEFAULT_CHARSET: Final = "utf-8"
"""Body encoding when the server names none, or one Python does not know."""

HTML_CONTENT_TYPES: Final = frozenset({"text/html", "application/xhtml+xml"})
"""Media types whose main text trafilatura extracts."""

PLAIN_TEXT_CONTENT_TYPE: Final = "text/plain"
"""Media type of plain text and of a real robots.txt (not an anti-bot page)."""

ALLOWED_CONTENT_TYPES: Final = HTML_CONTENT_TYPES | {PLAIN_TEXT_CONTENT_TYPE}
"""Media types read at all; PDFs, images and the rest are ``unsupported_content``."""

REDIRECT_STATUSES: Final = frozenset({301, 302, 303, 307, 308})
"""HTTP statuses followed as redirects when they carry a Location header."""

LOGIN_WALL_STATUSES: Final = frozenset({401, 403, 407})
"""Statuses meaning the page needs an account: the citizen should paste the text."""

PAYWALL_STATUSES: Final = frozenset({402})
"""Statuses meaning the page needs a payment: the citizen should paste the text."""

LOGIN_PATH: Final = re.compile(
    r"/(login|signin|sign-in|log-in|auth|accounts/login|checkpoint)(/|\.|$)",
    re.IGNORECASE,
)
"""Path of a login page; a redirect that lands there is a login wall (Facebook, X)."""

PASSWORD_INPUT: Final = re.compile(
    r"<input[^>]+type\s*=\s*[\"']?password", re.IGNORECASE
)
"""A password field; with little main text around it the page is a login form."""

LOGIN_WALL_MAX_TEXT_CHARS: Final = 500
"""Main text shorter than this next to a password field counts as a login wall."""

PAYWALL_MARKER: Final = re.compile(
    r"\"isAccessibleForFree\"\s*:\s*\"?false", re.IGNORECASE
)
"""schema.org flag that publishers set on paywalled articles."""

IPV4_EMBEDDING_PREFIXES: Final = (
    ipaddress.IPv6Network("64:ff9b::/96"),
    ipaddress.IPv6Network("::ffff:0:0:0/96"),
    ipaddress.IPv6Network("::/96"),
)
"""IPv6 prefixes whose last 32 bits are an IPv4 address, checked as such.

NAT64 well-known prefix, IPv4-translated (SIIT) and deprecated IPv4-compatible.
"""

IPV4_BITS: Final = 0xFFFFFFFF
"""Mask of the IPv4 address in the last 32 bits of an embedding IPv6 address."""

ROBOTS_AGENT: Final = "MeritumBot"
"""Product token looked up in robots.txt ``User-agent`` groups."""

USER_AGENT: Final = f"{ROBOTS_AGENT}/0.1 (+https://github.com/Meritum-HackNation2026)"
"""User-Agent header of every request; robots.txt groups match its product token."""

ROBOTS_PATH: Final = "/robots.txt"
"""Where each host's robots.txt lives (RFC 9309)."""

CONTENT_SIGNAL_USE: Final = "ai-input"
"""Content-Signal use that covers sources quoted as evidence by a model (RFC draft)."""

PASTE_TEXT_REASONS: Final = frozenset(
    {
        FetchFailureReason.LOGIN_WALL,
        FetchFailureReason.PAYWALL,
        FetchFailureReason.JAVASCRIPT_REQUIRED,
    }
)
"""Failures where the citizen is asked to paste the text instead of the link."""

NOT_FOUND_STATUSES: Final = frozenset({404, 410})
"""Statuses meaning the server has no such page (``not_found``, e.g. no robots.txt)."""

TDM_META_NAME: Final = "tdm-reservation"
"""TDMRep meta tag; ``content`` equal to ``TDM_RESERVED_VALUE`` reserves mining."""

TDM_RESERVED_VALUE: Final = "1"
"""TDMRep value of a reservation (W3C TDMRep); ``0`` means none."""

CONTENT_SIGNAL_DENIED: Final = "no"
"""Content-Signal answer that refuses a use (``ai-input=no``)."""

ROBOTS_META_NAME: Final = "robots"
"""Robots meta tag, read for the ``noai`` directive."""

NOAI_DIRECTIVE: Final = "noai"
"""Robots meta directive that opts the page out of AI use."""

ENV_PREFIX: Final = "MERITUM_FETCH_"
"""Prefix of every page fetcher setting in the environment."""

CRAWL4AI_TIMEOUT_S: Final = 30.0
"""Budget of one Crawl4AI render: a headless browser is slower than one GET."""

CRAWL4AI_CRAWL_PATH: Final = "/crawl"
"""Crawl4AI endpoint that renders a list of URLs and answers with the results."""

CRAWL4AI_MAX_REPLY_BYTES: Final = 4 * MAX_RESPONSE_BYTES
"""Largest Crawl4AI reply read; it carries the HTML plus markdown and metadata."""
