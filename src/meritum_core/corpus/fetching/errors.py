"""Failures of the page fetcher; their messages carry no network details.

Every failure is a ``technical_failure`` of the check. The message is the reason
code only: never the address, the resolved IP or the provider's error text.

Features:
    US-SPR-07, F-06
"""

from typing import Literal

from meritum_core.corpus.fetching.constants import PASTE_TEXT_REASONS
from meritum_core.corpus.fetching.models import FetchFailureReason


class PageFetchError(Exception):
    """A page could not be fetched; the check ends as ``technical_failure``.

    Args:
        reason: why; ``str(error)`` is this code and nothing else.

    Attributes:
        reason: why the fetch failed.
        check_status: the check outcome this failure maps to.

    Features:
        US-SPR-07, F-06
    """

    check_status: Literal["technical_failure"] = "technical_failure"

    def __init__(self, reason: FetchFailureReason) -> None:
        super().__init__(reason.value)
        self.reason = reason

    @property
    def asks_for_text(self) -> bool:
        """Whether the citizen should be asked to paste the text instead.

        Features:
            US-SPR-07
        """
        return self.reason in PASTE_TEXT_REASONS


class BlockedAddressError(PageFetchError):
    """The URL or a redirect points to an internal address (SSRF); nothing was sent.

    Features:
        US-SPR-07, F-06
    """


class LoginWallError(PageFetchError):
    """The page sits behind a login or a paywall; we never get around it.

    Features:
        US-SPR-07, F-06
    """


class JavaScriptRequiredError(PageFetchError):
    """The HTML has no main text without JavaScript; core/025 renders such pages.

    Features:
        US-SPR-07, F-06
    """

    def __init__(self) -> None:
        super().__init__(FetchFailureReason.JAVASCRIPT_REQUIRED)


class RobotsDisallowedError(PageFetchError):
    """robots.txt or its Content-Signal forbids fetching this source.

    Features:
        F-06
    """

    def __init__(self) -> None:
        super().__init__(FetchFailureReason.ROBOTS_DISALLOWED)
