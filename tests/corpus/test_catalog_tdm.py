"""The TDM check records the owner's opt-out in tdm_reservation, through the fetcher port."""

import asyncio

import pytest

from meritum_core.checks.contracts import CatalogEntry
from meritum_core.corpus.catalog import check_tdm
from meritum_core.corpus.fetching import (
    FetchedPage,
    FetchFailureReason,
    FetchPurpose,
    PageFetchError,
    RobotsDisallowedError,
)

SECONDARY = CatalogEntry(
    domain="fakenews.pl",
    publisher="Stowarzyszenie Demagog",
    publisher_id="fakenews",
    kind="fact_check",
    tier="secondary",
    license="prawo cytatu",
    ingest="rss",
    qualified_because="Sygnatariusz IFCN bez blokad dla robotów.",
)
PRIMARY = SECONDARY.model_copy(update={"tier": "primary", "kind": "instytucja"})


class FakeFetcher:
    def __init__(self, error: PageFetchError | None = None) -> None:
        self.error = error
        self.calls: list[tuple[str, FetchPurpose]] = []

    async def fetch(self, url: str, *, purpose: FetchPurpose) -> FetchedPage:
        self.calls.append((url, purpose))
        if self.error:
            raise self.error
        return FetchedPage(url=url, content_type="text/html", untrusted_text="tekst")


def run(entry: CatalogEntry, fetcher: FakeFetcher) -> CatalogEntry:
    return asyncio.run(check_tdm(entry, fetcher))


def test_fetches_the_domain_root_as_a_source() -> None:
    fetcher = FakeFetcher()
    assert run(SECONDARY, fetcher).tdm_reservation == "none"
    assert fetcher.calls == [("https://fakenews.pl", FetchPurpose.SOURCE)]


def test_secondary_source_with_reservation_is_excluded_with_reason() -> None:
    checked = run(SECONDARY, FakeFetcher(RobotsDisallowedError()))
    assert checked.tdm_reservation == "reserved"
    assert checked.excluded
    assert checked.exclusion_reason is not None


def test_primary_source_with_reservation_stays_included() -> None:
    checked = run(PRIMARY, FakeFetcher(RobotsDisallowedError()))
    assert checked.tdm_reservation == "reserved"
    assert not checked.excluded


@pytest.mark.parametrize(
    "reason", [FetchFailureReason.TIMEOUT, FetchFailureReason.HTTP_ERROR]
)
def test_failed_fetch_keeps_the_recorded_value(reason: FetchFailureReason) -> None:
    recorded = PRIMARY.model_copy(update={"tdm_reservation": "reserved"})
    checked = run(recorded, FakeFetcher(PageFetchError(reason)))
    assert checked == recorded


def test_lifted_reservation_brings_back_an_entry_the_check_excluded() -> None:
    reserved = run(SECONDARY, FakeFetcher(RobotsDisallowedError()))
    checked = run(reserved, FakeFetcher())
    assert checked.tdm_reservation == "none"
    assert not checked.excluded
    assert checked.exclusion_reason is None


def test_lifted_reservation_keeps_an_exclusion_with_another_reason() -> None:
    excluded = SECONDARY.model_copy(
        update={"excluded": True, "exclusion_reason": "Brak w IFCN i EFCSN."}
    )
    assert run(excluded, FakeFetcher()).excluded
