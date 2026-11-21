"""Rule 10: only the page fetcher's adapters reach the network over HTTP."""

import re
from collections.abc import Callable

type Forbid = Callable[[list[str], list[str]], None]

HTTP_CLIENTS = re.compile(
    r"^(httpx|httpcore|requests|aiohttp|urllib3|urllib\.request|http\.client)(\.|$)"
)
FETCHER = "meritum_core.corpus.fetching.adapters"


def test_only_the_page_fetcher_imports_an_http_client(
    own: list[str], modules: list[str], forbid: Forbid
) -> None:
    clients = [m for m in modules if HTTP_CLIENTS.match(m)]
    others = [m for m in own if not m.startswith(FETCHER)]
    assert clients
    forbid(others, clients)
