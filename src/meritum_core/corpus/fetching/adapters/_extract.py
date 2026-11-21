"""Turns a fetched response into a page: walls, media types and main text.

Features:
    US-SPR-07, F-06, ADR-12
"""

import warnings
from dataclasses import dataclass
from urllib.parse import urlsplit

from urllib3.exceptions import DependencyWarning

from meritum_core.corpus.fetching.constants import (
    ALLOWED_CONTENT_TYPES,
    HTML_CONTENT_TYPES,
    LOGIN_PATH,
    LOGIN_WALL_MAX_TEXT_CHARS,
    LOGIN_WALL_STATUSES,
    PASSWORD_INPUT,
    PAYWALL_MARKER,
    PAYWALL_STATUSES,
)
from meritum_core.corpus.fetching.errors import (
    FetchFailureReason,
    JavaScriptRequiredError,
    LoginWallError,
    PageFetchError,
)
from meritum_core.corpus.fetching.models import FetchedPage

with warnings.catch_warnings():
    # trafilatura's own downloader imports urllib3's optional SOCKS support; we
    # never use that downloader, only its extractor.
    warnings.simplefilter("ignore", DependencyWarning)
    import trafilatura


@dataclass(frozen=True)
class Response:
    """What the transport read: final URL, status, media type and body text.

    Attributes:
        url: the final URL as the caller sees it (host name, not IP).
        status: the HTTP status.
        content_type: the media type without parameters, lower case.
        text: the decoded body; empty when it was not read.

    Features:
        US-SPR-07, F-06
    """

    url: str
    status: int
    content_type: str
    text: str


def _check_walls(response: Response) -> None:
    if (
        LOGIN_PATH.search(urlsplit(response.url).path)
        or response.status in LOGIN_WALL_STATUSES
    ):
        raise LoginWallError(FetchFailureReason.LOGIN_WALL)
    if response.status in PAYWALL_STATUSES:
        raise LoginWallError(FetchFailureReason.PAYWALL)
    if not 200 <= response.status < 300:  # ruff: ignore[magic-value-comparison]  # the 2xx class
        raise PageFetchError(FetchFailureReason.HTTP_ERROR)
    if response.content_type not in ALLOWED_CONTENT_TYPES:
        raise PageFetchError(FetchFailureReason.UNSUPPORTED_CONTENT)


def _main_text(html: str) -> str:
    text = (trafilatura.extract(html) or "").strip()
    if PAYWALL_MARKER.search(html):
        raise LoginWallError(FetchFailureReason.PAYWALL)
    is_login_form = PASSWORD_INPUT.search(html) is not None
    if is_login_form and len(text) < LOGIN_WALL_MAX_TEXT_CHARS:
        raise LoginWallError(FetchFailureReason.LOGIN_WALL)
    if not text:
        raise JavaScriptRequiredError
    return text


def to_page(response: Response) -> FetchedPage:
    """Check the response for walls and errors and extract its main text.

    Args:
        response: the final response, after redirects.

    Returns:
        The page; its text is untrusted data.

    A login or paywall raises ``LoginWallError``, HTML without main text
    ``JavaScriptRequiredError``, an error status or media type ``PageFetchError``.

    Features:
        US-SPR-07, F-06, ADR-12
    """
    _check_walls(response)
    is_html = response.content_type in HTML_CONTENT_TYPES
    text = _main_text(response.text) if is_html else response.text.strip()
    return FetchedPage(
        url=response.url, content_type=response.content_type, untrusted_text=text
    )
