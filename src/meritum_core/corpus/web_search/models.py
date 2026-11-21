"""What live web search returns: addresses to fetch, never page content.

Features:
    US-KOR-04, F-13, ADR-07
"""

from pydantic import BaseModel

from meritum_core.checks.contracts import PublisherId


class WebSearchCandidate(BaseModel, frozen=True):
    """One address from a catalogue domain, to be fetched and only then cited.

    Attributes:
        url: the address the provider found; the page fetcher reads it.
        domain: the catalogue entry it matched (host with an optional path).
        publisher_id: the entry's publisher, for counting independent sources.

    Features:
        US-KOR-04, F-13, ADR-07
    """

    url: str
    domain: str
    publisher_id: PublisherId
