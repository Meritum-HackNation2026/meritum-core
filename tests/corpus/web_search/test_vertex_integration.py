"""Vertex AI Search on the real data store: local only, ``uv run pytest -m integration``.

Needs Application Default Credentials and the search app from meritum-infra
(infra#16): ``MERITUM_WEB_SEARCH_PROJECT`` and ``MERITUM_WEB_SEARCH_ENGINE``.
"""

import asyncio
import os

import pytest

from meritum_core.corpus.catalog import load_catalog
from meritum_core.corpus.web_search import (
    WebSearchSettings,
    build_web_search,
    catalog_entry_for,
)
from meritum_core.security import MaskedText


@pytest.mark.integration
def test_real_search_returns_only_catalogue_addresses() -> None:
    names = ("MERITUM_WEB_SEARCH_PROJECT", "MERITUM_WEB_SEARCH_ENGINE")
    if any(os.environ.get(name) is None for name in names):
        pytest.skip("MERITUM_WEB_SEARCH_PROJECT and _ENGINE are not set")
    catalog = load_catalog()
    search = build_web_search(WebSearchSettings(provider="vertex_search"), catalog)
    query = MaskedText(text="ostrzeżenie przed burzami", replaced=0)
    candidates = asyncio.run(search.search(query))
    assert candidates
    assert all(catalog_entry_for(c.url, catalog) for c in candidates)
