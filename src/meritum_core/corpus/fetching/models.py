"""What the page fetcher returns, why it fetches and why it fails.

Features:
    US-SPR-07, F-06
"""

from datetime import date
from enum import StrEnum

from pydantic import BaseModel


class FetchPurpose(StrEnum):
    """Why a page is fetched; sources honour robots.txt, a pasted link does not.

    Features:
        US-SPR-07, F-06
    """

    USER_LINK = "user_link"
    """A link the citizen pasted instead of the text (one page, on their behalf)."""
    SOURCE = "source"
    """A catalogue source, a search result or other page fetched by the system."""


class FetchFailureReason(StrEnum):
    """Why a page could not be fetched; the message of every fetch error.

    Features:
        US-SPR-07, F-06
    """

    UNSUPPORTED_URL = "unsupported_url"
    """Not an http(s) URL with a host, or it carries credentials."""
    BLOCKED_ADDRESS = "blocked_address"
    """The host is or resolves to a private, loopback, link-local or multicast IP."""
    REDIRECT_BLOCKED = "redirect_blocked"
    """A redirect pointed to such an address."""
    TOO_MANY_REDIRECTS = "too_many_redirects"
    """More redirects than ``MAX_REDIRECTS``."""
    TIMEOUT = "timeout"
    """The fetch took longer than its time limits."""
    UNREACHABLE = "unreachable"
    """DNS or the connection failed."""
    HTTP_ERROR = "http_error"
    """The server answered with an error status."""
    NOT_FOUND = "not_found"
    """The server has no such page (404 or 410)."""
    UNSUPPORTED_CONTENT = "unsupported_content"
    """The media type is not one of ``ALLOWED_CONTENT_TYPES``."""
    TOO_LARGE = "too_large"
    """The body is larger than ``MAX_RESPONSE_BYTES``."""
    LOGIN_WALL = "login_wall"
    """The page needs an account; the citizen should paste the text."""
    PAYWALL = "paywall"
    """The page needs a payment; the citizen should paste the text."""
    JAVASCRIPT_REQUIRED = "javascript_required"
    """No main text without running JavaScript; the core/025 adapter renders it."""
    ROBOTS_DISALLOWED = "robots_disallowed"
    """robots.txt or its Content-Signal forbids fetching the source."""


class FetchedPage(BaseModel, frozen=True):
    """Main text of one fetched page.

    The text is untrusted data written by a third party: it is quoted, never
    followed as instructions (ADR-12).

    Attributes:
        url: the final URL, after redirects.
        content_type: the media type of the response, without parameters.
        untrusted_text: the main text (trafilatura for HTML, the body for text).
        tdm_reserved: the page's meta tags reserve text and data mining.
        published_at: the publication date from the HTML metadata; None for
            plain text, a page without a date or one whose date is unreadable.

    Features:
        US-SPR-07, US-ZRD-05, F-06, ADR-12
    """

    url: str
    content_type: str
    untrusted_text: str
    tdm_reserved: bool = False
    published_at: date | None = None
