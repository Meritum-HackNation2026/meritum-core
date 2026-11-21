"""Fixtures for the web search tests: a small catalogue and recorded Vertex replies."""

import json
from collections.abc import Callable
from pathlib import Path

import httpx2
import pytest
from google.oauth2.credentials import Credentials

from meritum_core.checks.contracts import CatalogEntry
from meritum_core.corpus.web_search import (
    WebSearchPort,
    WebSearchSettings,
    build_web_search,
)

FIXTURES = Path(__file__).parent / "fixtures"

type Sent = list[httpx2.Request]
type Recorded = Callable[[int, str], tuple[WebSearchPort, Sent]]


def entry(domain: str, publisher_id: str, **extra: object) -> CatalogEntry:
    """A valid catalogue entry for ``domain``."""
    return CatalogEntry.model_validate(
        {
            "domain": domain,
            "publisher": f"Wydawca {domain}",
            "publisher_id": publisher_id,
            "kind": "instytucja",
            "tier": "primary",
            "license": "materiał urzędowy",
            "ingest": "web_search",
            "qualified_because": "Komunikaty urzędowe dla obywateli.",
            **extra,
        }
    )


@pytest.fixture
def catalog() -> tuple[CatalogEntry, ...]:
    return (
        entry("www.gov.pl/web/gov/ostrzezenia", "rcb"),
        entry("gov.pl", "gov"),
        entry("meteo.imgw.pl", "imgw"),
    )


@pytest.fixture
def recorded(catalog: tuple[CatalogEntry, ...]) -> Recorded:
    """Build Vertex AI Search through the factory; every call gets the same reply."""

    def build(status: int, name: str) -> tuple[WebSearchPort, Sent]:
        sent: Sent = []

        def reply(request: httpx2.Request) -> httpx2.Response:
            sent.append(request)
            payload = json.loads((FIXTURES / name).read_text(encoding="utf-8"))
            return httpx2.Response(status, json=payload)

        client = httpx2.AsyncClient(transport=httpx2.MockTransport(reply))
        token = Credentials(token="recorded")  # ruff: ignore[hardcoded-password-func-arg]  # fake token, no network
        settings = WebSearchSettings(
            provider="vertex_search", project="meritum-test", engine="meritum-web"
        )
        search = build_web_search(
            settings, catalog, credentials=token, http_client=client
        )
        return search, sent

    return build
