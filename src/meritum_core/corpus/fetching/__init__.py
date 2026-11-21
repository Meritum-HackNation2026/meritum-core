"""Page fetching: the only way Meritum reads a URL (corpus, checks, robots.txt).

Public API of the subdomain: re-exports only.

Features:
    US-SPR-07, F-06
"""

from meritum_core.corpus.fetching.errors import (
    BlockedAddressError,
    FetchFailureReason,
    JavaScriptRequiredError,
    LoginWallError,
    PageFetchError,
    RobotsDisallowedError,
)
from meritum_core.corpus.fetching.factory import build_page_fetcher
from meritum_core.corpus.fetching.models import FetchedPage, FetchPurpose
from meritum_core.corpus.fetching.ports import PageFetcherPort

__all__ = [
    "BlockedAddressError",
    "FetchFailureReason",
    "FetchPurpose",
    "FetchedPage",
    "JavaScriptRequiredError",
    "LoginWallError",
    "PageFetchError",
    "PageFetcherPort",
    "RobotsDisallowedError",
    "build_page_fetcher",
]
