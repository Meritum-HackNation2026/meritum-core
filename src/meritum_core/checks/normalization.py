"""Input normalization and the result-cache key shared by every channel.

The same post pasted in the web form, the extension or Discord differs in spaces,
quotes or a trailing URL. The backend's result cache and the channel-consistency
evaluation both key results by :func:`normalize_input`, so they agree.

Features: US-WTY-03, F-05, ADR-19
"""

import hashlib
import unicodedata
from dataclasses import dataclass
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from meritum_core.checks.constants import (
    DASHES,
    NORMALIZATION_VERSION,
    QUOTES,
    TRACKING_PARAMS,
    TRACKING_PREFIXES,
    URL_PATTERN,
    URL_SCHEMES,
    URL_TRAILING_PUNCTUATION,
    WHITESPACE,
)


@dataclass(frozen=True, slots=True)
class NormalizedInput:
    """An input in the form the result cache is keyed by.

    Attributes:
        text: The normalized text, without the post URL.
        post_url: The canonical post URL, kept as context and out of the key.
        cache_key: SHA-256 hex digest of the rules version and ``text``.

    Features: US-WTY-03, F-05, ADR-19
    """

    text: str
    post_url: str | None
    cache_key: str


def canonical_url(url: str) -> str | None:
    """Return ``url`` with a lowercase scheme and host, no fragment, no tracking.

    Args:
        url: An absolute http(s) URL.

    Returns:
        The canonical URL with the remaining query parameters sorted, or None
        when the scheme is not http(s).

    Features: US-WTY-03, F-05, ADR-19
    """
    parts = urlsplit(url.strip().rstrip(URL_TRAILING_PUNCTUATION))
    if parts.scheme.lower() not in URL_SCHEMES:
        return None
    query = sorted(
        (name, value)
        for name, value in parse_qsl(parts.query, keep_blank_values=True)
        if name.lower() not in TRACKING_PARAMS
        and not name.lower().startswith(TRACKING_PREFIXES)
    )
    return urlunsplit(
        (
            parts.scheme.lower(),
            parts.netloc.lower(),
            parts.path,
            urlencode(query),
            "",
        )
    )


def cache_key(text: str, *, version: int = NORMALIZATION_VERSION) -> str:
    """Hash normalized text with the rules version into a result-cache key.

    Args:
        text: Text already passed through :func:`normalize_input`.
        version: Version of the normalization rules.

    Returns:
        A 64-character SHA-256 hex digest.

    Features: US-WTY-03, F-05, ADR-19
    """
    return hashlib.sha256(f"{version}\n{text}".encode()).hexdigest()


def normalize_input(text: str, post_url: str | None = None) -> NormalizedInput:
    """Normalize a channel's input and derive its result-cache key.

    Applies Unicode NFC, ASCII quotes and dashes, and collapsed whitespace; cuts
    URLs out of the text. Channel, session and interface language never reach the
    key, so callers do not pass them.

    Args:
        text: The text as the channel received it.
        post_url: The post's URL when the channel sends it separately; otherwise
            the first URL found in ``text``.

    Returns:
        The normalized text, the canonical post URL and the cache key. Input
        that is only a URL is keyed by the canonical URL, so different posts
        never share an entry.

    Features: US-WTY-03, F-05, ADR-19
    """
    text = unicodedata.normalize("NFC", text).translate(str.maketrans(QUOTES | DASHES))
    urls = URL_PATTERN.findall(text)
    text = WHITESPACE.sub(" ", URL_PATTERN.sub(" ", text)).strip()
    url = post_url or next(iter(urls), None)
    canonical = canonical_url(url) if url is not None else None
    return NormalizedInput(
        text=text, post_url=canonical, cache_key=cache_key(text or canonical or "")
    )
