"""The text and data mining opt-out check of one catalogue entry.

Features:
    US-KOR-01, F-10, ADR-24
"""

from typing import Literal
from urllib.parse import urlsplit

from meritum_core.checks.contracts import CatalogEntry
from meritum_core.corpus.constants import TDM_EXCLUSION_REASON, TDM_SIGNAL_USES
from meritum_core.corpus.fetching import (
    FetchFailureReason,
    FetchPurpose,
    PageFetcherPort,
    PageFetchError,
    RobotsDisallowedError,
    content_signals,
)
from meritum_core.corpus.fetching.constants import ROBOTS_PATH

type _Reading = Literal["none", "reserved"] | None
"""What one owner signal says; None when it could not be read."""


def _reserves(signal: str) -> bool:
    pairs = (pair.partition("=") for pair in signal.lower().split(","))
    return any(u.strip() in TDM_SIGNAL_USES and a.strip() == "no" for u, _, a in pairs)


async def _robots_signal(root: str, fetcher: PageFetcherPort) -> _Reading:
    host_root = urlsplit(root)._replace(path="").geturl()  # domain may be a path prefix
    try:
        robots = await fetcher.fetch(
            host_root + ROBOTS_PATH, purpose=FetchPurpose.USER_LINK
        )
    except PageFetchError as error:
        return "none" if error.reason is FetchFailureReason.NOT_FOUND else None
    if robots.content_type != "text/plain":  # an anti-bot page, not robots.txt
        return None
    reserved = any(map(_reserves, content_signals(robots.untrusted_text)))
    return "reserved" if reserved else "none"


async def _meta_signal(root: str, fetcher: PageFetcherPort) -> _Reading:
    try:
        page = await fetcher.fetch(root, purpose=FetchPurpose.SOURCE)
    except RobotsDisallowedError:
        return "none"  # not crawled at all, so its meta tags reserve nothing
    except PageFetchError:
        return None
    return "reserved" if page.tdm_reserved else "none"


def _recorded(
    entry: CatalogEntry, reservation: Literal["none", "reserved"]
) -> CatalogEntry:
    excluded, reason = entry.excluded, entry.exclusion_reason
    if reservation == "reserved" and entry.tier == "secondary" and not excluded:
        excluded, reason = True, TDM_EXCLUSION_REASON
    if reservation == "none" and reason == TDM_EXCLUSION_REASON:
        excluded, reason = False, None
    update = {
        "tdm_reservation": reservation,
        "excluded": excluded,
        "exclusion_reason": reason,
    }
    return CatalogEntry.model_validate(entry.model_copy(update=update).model_dump())


async def check_tdm(entry: CatalogEntry, fetcher: PageFetcherPort) -> CatalogEntry:
    """Read the owner's text and data mining opt-out and record it in the entry.

    The opt-out (art. 4 of directive 2019/790) is ``ai-train=no`` or
    ``ai-input=no`` in a robots.txt Content-Signal, or a ``tdm-reservation``
    or ``noai`` meta tag on the entry's root page. A ``Disallow`` alone blocks
    crawling, not mining. A secondary source with a reservation is excluded with
    a reason (ADR-24) and brought back when the owner lifts it. When either
    signal cannot be read and none reserves, the entry stays as recorded.

    Args:
        entry: the catalogue entry to check.
        fetcher: the SSRF-safe page fetcher.

    Returns:
        A copy of ``entry`` with ``tdm_reservation`` set, excluded when required.

    Features:
        US-KOR-01, F-10, ADR-24
    """
    root = f"https://{entry.domain}"
    readings = {await _robots_signal(root, fetcher), await _meta_signal(root, fetcher)}
    if "reserved" in readings:
        return _recorded(entry, "reserved")
    if None in readings:
        return entry
    return _recorded(entry, "none")
