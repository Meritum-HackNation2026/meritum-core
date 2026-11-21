"""Steps for the source-catalogue scenarios of features/corpus.feature.

The catalogue is a temporary YAML file; the owner's server is an in-process httpx
handler and DNS a table, so nothing leaves the process.
"""

import asyncio
import ipaddress
import tempfile
from pathlib import Path

import httpx
from behave import given, then, when
from behave.runner import Context
from pydantic import ValidationError

from meritum_core.checks.contracts import CatalogEntry
from meritum_core.corpus.catalog import InvalidCatalogError, check_tdm, load_catalog
from meritum_core.corpus.fetching import build_page_fetcher

type Address = ipaddress.IPv4Address | ipaddress.IPv6Address

SECONDARY = {
    "domain": "fakenews.example",
    "publisher": "Redakcja fact-checkingowa",
    "publisher_id": "fakenews-example",
    "kind": "fact_check",
    "tier": "secondary",
    "license": "prawo cytatu",
    "ingest": "rss",
    "qualified_because": "Sygnatariusz IFCN, cytowany krótko z linkiem.",
}
ROBOTS = "User-agent: *\nContent-Signal: search=yes, ai-input=no\nAllow: /\n"


@given("pozycja katalogu z excluded = true i pustym exclusion_reason")
def given_excluded_without_reason(context: Context) -> None:
    """A catalogue file whose second entry is excluded with an empty reason."""
    folder = Path(tempfile.mkdtemp())
    context.catalog = folder / "catalog.yaml"
    context.catalog.write_text(
        "entries:\n"
        "  - {domain: a.example, publisher: Urząd A, publisher_id: urzad-a,"
        " kind: instytucja, tier: primary, license: materiał urzędowy,"
        " ingest: static, qualified_because: Komunikaty urzędu A.}\n"
        "  - {domain: b.example, publisher: Urząd B, publisher_id: urzad-b,"
        " kind: instytucja, tier: primary, license: materiał urzędowy,"
        " ingest: static, qualified_because: Komunikaty urzędu B.,"
        " excluded: true, exclusion_reason: ''}\n",
        encoding="utf-8",
    )


@when("katalog jest walidowany")
def when_catalog_validated(context: Context) -> None:
    """Load the catalogue file, keeping the error."""
    try:
        load_catalog(context.catalog)
    except InvalidCatalogError as error:
        context.error = error
    else:
        context.error = None


@then("walidacja kończy się błędem wskazującym tę pozycję")
def then_error_names_entry(context: Context) -> None:
    """The error names the excluded entry by index and domain."""
    assert context.error is not None
    assert "entries[1] b.example" in str(context.error)


@given(
    "źródło wtórne (tier secondary) z zastrzeżeniem eksploracji tekstów i danych"
    " w robots.txt albo Content-Signal"
)
def given_reserved_secondary(context: Context) -> None:
    """A secondary source whose robots.txt says ``ai-input=no``."""

    def handle(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/robots.txt":
            return httpx.Response(200, text=ROBOTS)
        return httpx.Response(200, html="<html><body>tekst</body></html>")

    async def resolve(_host: str) -> list[Address]:  # ruff: ignore[unused-async]  # Resolver is async
        return [ipaddress.ip_address("93.184.215.14")]

    context.fetcher = build_page_fetcher(
        resolver=resolve, transport=httpx.MockTransport(handle)
    )
    context.entry = CatalogEntry.model_validate(SECONDARY)


@when("kurator uruchamia kontrolę katalogu")
def when_curator_checks(context: Context) -> None:
    """Run the TDM check on the entry."""
    context.checked = asyncio.run(check_tdm(context.entry, context.fetcher))


@then(
    "pozycja ma tdm_reservation = reserved, excluded = true"
    " i exclusion_reason z powodem"
)
def then_entry_excluded(context: Context) -> None:
    """The check recorded the reservation and excluded the entry with a reason."""
    checked = context.checked
    assert checked.tdm_reservation == "reserved"
    assert checked.excluded
    assert checked.exclusion_reason is not None


@then("walidacja CatalogEntry odrzuca taką pozycję bez wykluczenia")
def then_contract_rejects_kept_entry(context: Context) -> None:
    """Keeping the reserved secondary source breaks the contract."""
    kept = context.checked.model_dump() | {"excluded": False, "exclusion_reason": None}
    rejected = False
    try:
        CatalogEntry.model_validate(kept)
    except ValidationError:
        rejected = True
    assert rejected, "a reserved secondary source passed validation"
