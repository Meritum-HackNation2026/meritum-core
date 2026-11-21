"""Turns a fetched response into a page: walls, media types and main text.

Features:
    US-SPR-07, F-06, ADR-12
"""

import warnings
from dataclasses import dataclass
from datetime import date
from urllib.parse import urlsplit

from urllib3.exceptions import DependencyWarning

from meritum_core.corpus.fetching.adapters._meta import meta_reserves_mining
from meritum_core.corpus.fetching.constants import (
    ALLOWED_CONTENT_TYPES,
    HTML_CONTENT_TYPES,
    LOGIN_PATH,
    LOGIN_WALL_MAX_TEXT_CHARS,
    LOGIN_WALL_STATUSES,
    NOT_FOUND_STATUSES,
    PASSWORD_INPUT,
    PAYWALL_MARKER,
    PAYWALL_STATUSES,
)
from meritum_core.corpus.fetching.errors import (
    JavaScriptRequiredError,
    LoginWallError,
    PageFetchError,
    PaywallError,
)
from meritum_core.corpus.fetching.models import FetchedPage, FetchFailureReason

with warnings.catch_warnings():
    # trafilatura's own downloader imports urllib3's optional SOCKS support; we
    # never use that downloader, only its extractor.
    warnings.simplefilter("ignore", DependencyWarning)
    import trafilatura


@dataclass(frozen=True)
class RawResponse:
    """What the transport read for one hop, before any page rule.

    Attributes:
        url: the URL as the caller sees it (host name, not the pinned IP).
        status: the HTTP status.
        content_type: the media type without parameters, lower case.
        text: the decoded body; empty when it was not read.
        location: the redirect target; empty when this is not a redirect.
        redirected: whether a redirect led here.

    Features:
        US-SPR-07, F-06
    """

    url: str
    status: int
    content_type: str = ""
    text: str = ""
    location: str = ""
    redirected: bool = False

    @property
    def is_success(self) -> bool:
        """Whether the status is in the 2xx class.

        Features:
            US-SPR-07, F-06
        """
        return 200 <= self.status < 300  # ruff: ignore[magic-value-comparison]  # the 2xx class

    @property
    def is_client_error(self) -> bool:
        """Whether the status is in the 4xx class.

        Features:
            F-06
        """
        return 400 <= self.status < 500  # ruff: ignore[magic-value-comparison]  # the 4xx class


def _check_walls(response: RawResponse) -> None:
    on_login_path = LOGIN_PATH.search(urlsplit(response.url).path) is not None
    landed_on_login = response.redirected and on_login_path
    if landed_on_login or response.status in LOGIN_WALL_STATUSES:
        raise LoginWallError(FetchFailureReason.LOGIN_WALL)
    if response.status in PAYWALL_STATUSES:
        raise PaywallError
    if response.status in NOT_FOUND_STATUSES:
        raise PageFetchError(FetchFailureReason.NOT_FOUND)
    if not response.is_success:
        raise PageFetchError(FetchFailureReason.HTTP_ERROR)
    if response.content_type not in ALLOWED_CONTENT_TYPES:
        raise PageFetchError(FetchFailureReason.UNSUPPORTED_CONTENT)


def _main_text(html: str) -> str:
    text = (trafilatura.extract(html) or "").strip()
    if PAYWALL_MARKER.search(html):
        raise PaywallError
    is_login_form = PASSWORD_INPUT.search(html) is not None
    if is_login_form and len(text) < LOGIN_WALL_MAX_TEXT_CHARS:
        raise LoginWallError(FetchFailureReason.LOGIN_WALL)
    if not text:
        raise JavaScriptRequiredError
    return text


def _published_at(html: str) -> date | None:
    # extensive=False: metadata and markup only, htmldate guesses nothing from the text
    found = trafilatura.extract_metadata(html, extensive=False).date
    return None if found is None else date.fromisoformat(found)


def to_page(response: RawResponse) -> FetchedPage:
    """Check the response for walls and errors and extract its main text and date.

    Args:
        response: the final response, after redirects.

    Returns:
        The page; its text is untrusted data, its date comes from the HTML metadata.

    Raises:
        LoginWallError: A login stands in front of the content.
        PaywallError: A paywall stands in front of the content.
        JavaScriptRequiredError: The HTML has no main text without JavaScript.
        PageFetchError: An error status or an unsupported media type.

    Features:
        US-SPR-07, US-ZRD-05, F-06, ADR-12
    """  # ruff: ignore[docstring-extraneous-exception]  # raised by the helpers it calls
    _check_walls(response)
    is_html = response.content_type in HTML_CONTENT_TYPES
    text = _main_text(response.text) if is_html else response.text.strip()
    return FetchedPage(
        url=response.url,
        content_type=response.content_type,
        untrusted_text=text,
        tdm_reserved=is_html and meta_reserves_mining(response.text),
        published_at=_published_at(response.text) if is_html else None,
    )
