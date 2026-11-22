"""Limits and the Vertex AI Search setup of live web search, each one documented.

Features:
    US-KOR-04, US-WDR-02, F-13, ADR-07
"""

from typing import Final

ENV_PREFIX: Final = "MERITUM_WEB_SEARCH_"
"""Prefix of every web search setting in the environment."""

SEARCH_TIMEOUT_S: Final = 10.0
"""Wall-clock budget of one search; past it the port raises WebSearchTimeoutError."""

MAX_QUERIES_PER_MINUTE: Final = 60
"""Searches one built port sends in any 60 s window; more raise WebSearchRateLimitError.

Build the port once per process (``build_web_search``) so this is a per-process cap.
"""

RATE_WINDOW_S: Final = 60.0
"""Length of the sliding window ``MAX_QUERIES_PER_MINUTE`` counts in."""

DEFAULT_RESULTS: Final = 10
"""Addresses asked from the provider per search: basic website search's default."""

MAX_RESULTS: Final = 25
"""Most addresses one search may ask for: the basic website search maximum."""

WEB_SCHEMES: Final = frozenset({"http", "https"})
"""Schemes a candidate may have; anything else is dropped before the fetcher."""

WWW_PREFIX: Final = "www."
"""Host prefix ignored when a candidate is matched against the catalogue."""

VERTEX_ENDPOINT: Final = "https://discoveryengine.googleapis.com/v1"
"""REST endpoint of Vertex AI Search (Discovery Engine) for the ``global`` location."""

VERTEX_LOCATION: Final = "global"
"""Location of the website data store; basic website search runs only there (not EU)."""

VERTEX_COLLECTION: Final = "default_collection"
"""Collection of the search app created by meritum-infra (infra#16)."""

VERTEX_SERVING_CONFIG: Final = "default_search"
"""Serving config of the search app that answers ``:search``."""

VERTEX_SCOPES: Final = ("https://www.googleapis.com/auth/cloud-platform",)
"""OAuth scopes the adapter asks Application Default Credentials for."""

RESOURCE_ID_PATTERN: Final = r"^[a-z0-9][a-z0-9_-]*$"
"""Project and engine ids: plain path segments, so settings cannot reshape the URL."""

CONTRACT_QUERY: Final = "ostrzeżenie przed burzami"
"""Query the provider contract sends; the adapter under test must find results."""

DOT_SEGMENTS: Final = frozenset({".", ".."})
"""Path segments a client resolves away; a candidate holding one is dropped, or
``/allowed/../other`` would pass the path filter and fetch ``/other``."""

PATH_SEPARATORS: Final = frozenset({"/", "\\", ";"})
"""Separators a segment may not hold once decoded (``%2f``, ``%5c``, ``..;``): a
server that splits on them would see other segments than the path filter did."""

SEARXNG_SEARCH_PATH: Final = "search"
"""Path of the SearXNG search endpoint, joined to ``MERITUM_WEB_SEARCH_SEARXNG_URL``."""

SEARXNG_FORMAT: Final = "json"
"""Reply format asked from SearXNG; the instance must list it in ``search.formats``."""

SITE_JOINER: Final = " OR "
"""Joins the ``site:`` operators that keep a SearXNG query on catalogue hosts."""

LINKUP_ENDPOINT: Final = "https://api.linkup.so/v1/search"
"""REST endpoint of Linkup search; the optional adapter behind a key and a switch."""

LINKUP_DEPTH: Final = "standard"
"""Linkup search depth: one pass, the cheaper of ``standard`` and ``deep``."""

LINKUP_OUTPUT: Final = "searchResults"
"""Linkup output type that returns result addresses, not a sourced answer."""
