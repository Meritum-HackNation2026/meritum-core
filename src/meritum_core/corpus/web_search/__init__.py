"""Live web search: catalogue pages for fresh claims, behind one port.

Public API of the subdomain: re-exports only. A search gives addresses only;
the page fetcher reads them, honouring robots.txt and Content-Signal, before
anything is cited (ADR-07).

Features:
    US-KOR-04, US-WDR-02, F-13, ADR-07
"""

from meritum_core.corpus.web_search.contract import provider_contract_violations
from meritum_core.corpus.web_search.domains import catalog_entry_for
from meritum_core.corpus.web_search.errors import (
    WebSearchError,
    WebSearchRateLimitError,
    WebSearchTimeoutError,
    WebSearchUnavailableError,
)
from meritum_core.corpus.web_search.factory import build_web_search
from meritum_core.corpus.web_search.models import WebSearchCandidate
from meritum_core.corpus.web_search.ports import WebSearchPort, WebSearchProviderPort
from meritum_core.corpus.web_search.settings import (
    WebSearchProvider,
    WebSearchSettings,
)

__all__ = [
    "WebSearchCandidate",
    "WebSearchError",
    "WebSearchPort",
    "WebSearchProvider",
    "WebSearchProviderPort",
    "WebSearchRateLimitError",
    "WebSearchSettings",
    "WebSearchTimeoutError",
    "WebSearchUnavailableError",
    "build_web_search",
    "catalog_entry_for",
    "provider_contract_violations",
]
