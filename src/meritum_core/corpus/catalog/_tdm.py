"""The text and data mining opt-out check of one catalogue entry.

Features:
    US-KOR-01, F-10, ADR-24
"""

from typing import Literal

from meritum_core.checks.contracts import CatalogEntry
from meritum_core.corpus.constants import TDM_EXCLUSION_REASON
from meritum_core.corpus.fetching import (
    FetchPurpose,
    PageFetcherPort,
    PageFetchError,
    RobotsDisallowedError,
)

type _Reservation = Literal["none", "reserved"]


async def _reservation(url: str, fetcher: PageFetcherPort) -> _Reservation | None:
    try:
        await fetcher.fetch(url, purpose=FetchPurpose.SOURCE)
    except RobotsDisallowedError:
        return "reserved"
    except PageFetchError:
        return None  # timeout, error page: says nothing about the opt-out
    return "none"


def _update(entry: CatalogEntry, reservation: _Reservation) -> dict[str, object]:
    update: dict[str, object] = {"tdm_reservation": reservation}
    if reservation == "reserved" and entry.tier == "secondary" and not entry.excluded:
        update |= {"excluded": True, "exclusion_reason": TDM_EXCLUSION_REASON}
    excluded_by_check = entry.exclusion_reason == TDM_EXCLUSION_REASON
    if reservation == "none" and excluded_by_check:
        update |= {"excluded": False, "exclusion_reason": None}
    return update


async def check_tdm(entry: CatalogEntry, fetcher: PageFetcherPort) -> CatalogEntry:
    """Fetch the entry's root as a source and record the owner's TDM opt-out.

    The fetcher honours robots.txt and its Content-Signal for sources; a refusal
    (``Disallow`` or ``ai-input=no``) is the machine-readable reservation of
    art. 4 of directive 2019/790. A secondary source with a reservation is
    excluded with a reason (ADR-24), and brought back when the owner lifts it.
    Any other fetch failure leaves the entry as recorded.

    Args:
        entry: the catalogue entry to check.
        fetcher: the SSRF-safe page fetcher.

    Returns:
        A copy of ``entry`` with ``tdm_reservation`` set, excluded when required.

    Features:
        US-KOR-01, F-10, ADR-24
    """
    reservation = await _reservation(f"https://{entry.domain}", fetcher)
    if reservation is None:
        return entry
    return CatalogEntry.model_validate(entry.model_dump() | _update(entry, reservation))
