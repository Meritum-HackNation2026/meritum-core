"""Rule 10: only the page fetcher (its adapters and factory) uses an HTTP client."""

import re
from collections.abc import Callable

type Forbid = Callable[[list[str], list[str]], None]

HTTP_CLIENTS = re.compile(
    r"^(httpx|httpcore|requests|aiohttp|urllib3|urllib\.request|http\.client)(\.|$)"
)
FETCHER = re.compile(r"^meritum_core\.corpus\.fetching\.(adapters|factory)(\.|$)")


def test_only_the_page_fetcher_imports_an_http_client(
    own: list[str], modules: list[str], forbid: Forbid
) -> None:
    clients = [m for m in modules if HTTP_CLIENTS.match(m)]
    others = [m for m in own if not FETCHER.match(m)]
    assert clients
    forbid(others, clients)
