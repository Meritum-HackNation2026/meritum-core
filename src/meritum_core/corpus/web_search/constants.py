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
