"""Page fetching: the only way Meritum reads a URL (corpus, checks, robots.txt).

Public API of the subdomain: re-exports only.

Features:
    US-SPR-07, F-06
"""

from meritum_core.corpus.fetching.errors import (
    BlockedAddressError,
    JavaScriptRequiredError,
    LoginWallError,
    PageFetchError,
    PaywallError,
    RobotsDisallowedError,
)
from meritum_core.corpus.fetching.factory import build_page_fetcher
from meritum_core.corpus.fetching.models import (
    FetchedPage,
    FetchFailureReason,
    FetchPurpose,
)
from meritum_core.corpus.fetching.ports import PageFetcherPort, Resolver
from meritum_core.corpus.fetching.robots import content_signals, signal_denies
from meritum_core.corpus.fetching.settings import FetchingSettings

__all__ = [
    "BlockedAddressError",
    "FetchFailureReason",
    "FetchPurpose",
    "FetchedPage",
    "FetchingSettings",
    "JavaScriptRequiredError",
    "LoginWallError",
    "PageFetchError",
    "PageFetcherPort",
    "PaywallError",
    "Resolver",
    "RobotsDisallowedError",
    "build_page_fetcher",
    "content_signals",
    "signal_denies",
]
