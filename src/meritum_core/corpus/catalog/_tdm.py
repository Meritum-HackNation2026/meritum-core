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

type _Reservation = Literal["none", "reserved", "unknown"]


async def _reservation(url: str, fetcher: PageFetcherPort) -> _Reservation:
    try:
        await fetcher.fetch(url, purpose=FetchPurpose.SOURCE)
    except RobotsDisallowedError:
        return "reserved"
    except PageFetchError:
        return "unknown"
    return "none"


async def check_tdm(entry: CatalogEntry, fetcher: PageFetcherPort) -> CatalogEntry:
    """Fetch the entry's root as a source and record the owner's TDM opt-out.

    The fetcher honours robots.txt and its Content-Signal for sources, so a
    refusal means the owner reserved mining; any other failure leaves it unknown.
    A secondary source with a reservation is excluded with a reason (ADR-24).

    Args:
        entry: the catalogue entry to check.
        fetcher: the SSRF-safe page fetcher.

    Returns:
        A copy of ``entry`` with ``tdm_reservation`` set, excluded when required.

    Features:
        US-KOR-01, F-10, ADR-24
    """
    reservation = await _reservation(f"https://{entry.domain}", fetcher)
    update: dict[str, object] = {"tdm_reservation": reservation}
    must_exclude = reservation == "reserved" and entry.tier == "secondary"
    if must_exclude and not entry.excluded:
        update |= {"excluded": True, "exclusion_reason": TDM_EXCLUSION_REASON}
    return CatalogEntry.model_validate(entry.model_dump() | update)
