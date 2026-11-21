"""The TDM check records the owner's opt-out in tdm_reservation, through the fetcher port."""

import asyncio

import pytest

from meritum_core.checks.contracts import CatalogEntry
from meritum_core.corpus.catalog import check_tdm
from meritum_core.corpus.fetching import (
    FetchedPage,
    FetchFailureReason,
    FetchPurpose,
    JavaScriptRequiredError,
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
    tdm_reservation="none",
)
PRIMARY = SECONDARY.model_copy(update={"tier": "primary", "kind": "instytucja"})
ROBOTS = "https://fakenews.pl/robots.txt"
ROOT = "https://fakenews.pl"

type Answer = FetchedPage | PageFetchError


def text(body: str, content_type: str = "text/plain") -> FetchedPage:
    return FetchedPage(url=ROBOTS, content_type=content_type, untrusted_text=body)


def html(*, reserved: bool = False) -> FetchedPage:
    return FetchedPage(
        url=ROOT, content_type="text/html", untrusted_text="t", tdm_reserved=reserved
    )


class FakeFetcher:
    def __init__(self, robots: Answer, root: Answer) -> None:
        self.answers = {ROBOTS: robots, ROOT: root}
        self.calls: list[tuple[str, FetchPurpose]] = []

    async def fetch(self, url: str, *, purpose: FetchPurpose) -> FetchedPage:
        self.calls.append((url, purpose))
        answer = self.answers[url]
        if isinstance(answer, PageFetchError):
            raise answer
        return answer


def run(entry: CatalogEntry, robots: Answer, root: Answer) -> CatalogEntry:
    return asyncio.run(check_tdm(entry, FakeFetcher(robots, root)))


NO_ROBOTS = PageFetchError(FetchFailureReason.NOT_FOUND)


def test_reads_robots_txt_and_fetches_the_root_as_a_source() -> None:
    fetcher = FakeFetcher(text("User-agent: *\nAllow: /"), html())
    checked = asyncio.run(check_tdm(SECONDARY, fetcher))
    assert checked.tdm_reservation == "none"
    assert fetcher.calls == [
        (ROBOTS, FetchPurpose.USER_LINK),
        (ROOT, FetchPurpose.SOURCE),
    ]


def test_robots_txt_of_a_path_prefix_comes_from_the_host_root() -> None:
    entry = PRIMARY.model_copy(update={"domain": "www.gov.pl/web/rcb"})
    fetcher = FakeFetcher(NO_ROBOTS, html())
    fetcher.answers = {
        "https://www.gov.pl/robots.txt": NO_ROBOTS,
        "https://www.gov.pl/web/rcb": html(),
    }
    assert asyncio.run(check_tdm(entry, fetcher)).tdm_reservation == "none"


@pytest.mark.parametrize("signal", ["ai-train=no, search=yes", "ai-input=no"])
def test_content_signal_reservation_excludes_a_secondary_source(signal: str) -> None:
    robots = text(f"User-agent: *\nContent-Signal: {signal}\nAllow: /")
    checked = run(SECONDARY, robots, RobotsDisallowedError())
    assert checked.tdm_reservation == "reserved"
    assert checked.excluded
    assert checked.exclusion_reason is not None


def test_meta_tag_reservation_keeps_a_primary_source_included() -> None:
    checked = run(PRIMARY, NO_ROBOTS, html(reserved=True))
    assert checked.tdm_reservation == "reserved"
    assert not checked.excluded


def test_disallow_alone_is_not_a_mining_reservation() -> None:
    checked = run(
        SECONDARY, text("User-agent: *\nDisallow: /"), RobotsDisallowedError()
    )
    assert checked.tdm_reservation == "none"
    assert not checked.excluded


@pytest.mark.parametrize(
    ("robots", "root"),
    [
        (PageFetchError(FetchFailureReason.HTTP_ERROR), html()),
        (text("<html>Incapsula</html>", "text/html"), html()),
        (NO_ROBOTS, JavaScriptRequiredError()),
        (NO_ROBOTS, PageFetchError(FetchFailureReason.TIMEOUT)),
    ],
)
def test_unreadable_owner_signals_keep_the_recorded_value(
    robots: Answer, root: Answer
) -> None:
    recorded = PRIMARY.model_copy(update={"tdm_reservation": "reserved"})
    assert run(recorded, robots, root) == recorded


def test_lifted_reservation_brings_back_an_entry_the_check_excluded() -> None:
    reserved = run(SECONDARY, NO_ROBOTS, html(reserved=True))
    checked = run(reserved, NO_ROBOTS, html())
    assert checked.tdm_reservation == "none"
    assert not checked.excluded
    assert checked.exclusion_reason is None


def test_lifted_reservation_keeps_an_exclusion_with_another_reason() -> None:
    excluded = SECONDARY.model_copy(
        update={"excluded": True, "exclusion_reason": "Brak w IFCN i EFCSN."}
    )
    assert run(excluded, NO_ROBOTS, html()).excluded
