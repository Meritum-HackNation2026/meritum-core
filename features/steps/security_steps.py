"""Steps for features/security.feature: they mask text through the public API.

Sensitive Data Protection runs through the factory on a recorded reply (an httpx2
mock transport), so nothing leaves the process.
"""

import asyncio
import logging
from datetime import date
from pathlib import Path
from typing import override

import httpx2
from behave import given, then, when
from behave.runner import Context
from google.oauth2.credentials import Credentials

from meritum_core.corpus import CorpusSearchPort, Passage
from meritum_core.security import (
    NullPiiGate,
    PiiGateSettings,
    build_pii_gate,
    mask_personal_data,
)

FIXTURES = Path(__file__).parents[2] / "tests" / "security" / "fixtures"
ADDRESS_TEXT = (
    "Mieszkam przy ul. Marszałkowskiej 12/4, 00-590 Warszawa i widziałem, "
    "że szczepionki zawierają chipy."
)


class _Records(logging.Handler):
    def __init__(self) -> None:
        super().__init__(logging.INFO)
        self.lines: list[str] = []

    @override
    def emit(self, record: logging.LogRecord) -> None:
        self.lines.append(record.getMessage())


def _mask(context: Context) -> None:
    handler = _Records()
    log = logging.getLogger("meritum_core.security.pii")
    log.addHandler(handler)
    log.setLevel(logging.INFO)
    try:
        context.masked = asyncio.run(mask_personal_data(context.raw_text, context.gate))
    finally:
        log.removeHandler(handler)
    context.log_lines = handler.lines


@given('tekst do maskowania "{text}"')
def given_text_to_mask(context: Context, text: str) -> None:
    """Remember the citizen's text; the gate is the default one (no DLP)."""
    context.raw_text = text
    context.gate = build_pii_gate(PiiGateSettings())


@given("wdrożenie bez konfiguracji DLP")
def given_no_dlp(context: Context) -> None:
    """Default settings, and a text with an address and a phone number."""
    context.raw_text = f"{ADDRESS_TEXT} Dzwoń: 601 234 567."
    context.gate = build_pii_gate(PiiGateSettings())


@when("system maskuje tekst")
def when_system_masks(context: Context) -> None:
    """Mask the remembered text with the configured gate."""
    _mask(context)


def _recorded_dlp(context: Context) -> None:
    """Build Sensitive Data Protection answering with the recorded reply."""
    reply = (FIXTURES / "dlp-identifiers.json").read_bytes()
    context.sent = []

    def answer(request: httpx2.Request) -> httpx2.Response:
        context.sent.append(request)
        return httpx2.Response(200, content=reply)

    settings = PiiGateSettings(gate="sdp", project="meritum-test")
    context.gate = build_pii_gate(
        settings,
        credentials=Credentials(token="recorded"),  # ruff: ignore[hardcoded-password-func-arg]  # fake token, no network
        http_client=httpx2.AsyncClient(transport=httpx2.MockTransport(answer)),
    )


@given("bramka DLP z projektem z konfiguracji")
def given_dlp_with_project(context: Context) -> None:
    """Sensitive Data Protection configured with the project ``meritum-test``."""
    context.raw_text = ADDRESS_TEXT
    _recorded_dlp(context)


@when("system maskuje tekst z włączoną bramką DLP")
def when_system_masks_with_dlp(context: Context) -> None:
    """Mask through Sensitive Data Protection answering with a recorded reply."""
    _recorded_dlp(context)
    _mask(context)


@then("żądanie do DLP niesie ten projekt jako projekt limitów")
def then_request_names_quota_project(context: Context) -> None:
    """The quota project header names the configured project."""
    [request] = context.sent
    assert request.headers["x-goog-user-project"] == "meritum-test", request.headers


@then('wynik zawiera "{phone}", "{email}" i "{pesel}" zamiast tych danych')
def then_markers_replace_data(
    context: Context, phone: str, email: str, pesel: str
) -> None:
    """Every marker is present and no personal data is left."""
    masked = context.masked.text
    assert all(marker in masked for marker in (phone, email, pesel)), masked
    secrets = ("601 234 567", "jan.kowalski@example.pl", "44051401359", "ABA300000")
    for secret in secrets:
        assert secret not in masked, masked


@then("reszta tekstu jest bez zmian")
def then_rest_is_unchanged(context: Context) -> None:
    """Only the personal data changed."""
    expected = "Dzwonił z [telefon], pisz na [e-mail], PESEL [PESEL]"
    assert context.masked.text == expected, context.masked.text


@then("liczba z błędną sumą kontrolną PESEL zostaje bez zmian")
def then_number_is_kept(context: Context) -> None:
    """A number with a bad PESEL checksum is not personal data."""
    assert context.masked.text == context.raw_text, context.masked.text


@then("wynik jest identyczny z tekstem wejściowym")
def then_text_is_unchanged(context: Context) -> None:
    """Amounts are no personal data: nothing is replaced."""
    assert context.masked.text == context.raw_text, context.masked.text
    assert context.masked.replaced == 0


@then('wynik zawiera "{kept}"')
def then_result_keeps(context: Context, kept: str) -> None:
    """A public figure's name stays in the masked text."""
    assert kept in context.masked.text, context.masked.text


@then('oba numery są zastąpione znacznikiem "{marker}"')
def then_both_phones_are_masked(context: Context, marker: str) -> None:
    """Prefixed mobile and landline numbers are both replaced."""
    expected = f"Dzwoń na {marker} albo {marker}"
    assert context.masked.text == expected, context.masked.text


class _RecordingCorpus(CorpusSearchPort):
    """Corpus search that records the query it was given (no passages)."""

    def __init__(self) -> None:
        self.queries: list[str] = []

    @override
    async def search(
        self, query: str, *, claim_date: date, corpus_version: str, limit: int = 5
    ) -> list[Passage]:
        self.queries.append(query)
        return []


@given('twierdzenie "{claim}" po maskowaniu')
def given_masked_claim(context: Context, claim: str) -> None:
    """Mask the claim as the backend does before the workflow starts."""
    context.claim = asyncio.run(mask_personal_data(claim, NullPiiGate())).text


@when("system buduje zapytanie do wyszukiwania dowodów")
def when_system_builds_query(context: Context) -> None:
    """The masked claim is the corpus query (``CorpusSearchPort.search``)."""
    corpus = _RecordingCorpus()
    asyncio.run(
        corpus.search(context.claim, claim_date=date(2025, 1, 1), corpus_version="v1")
    )
    [context.query] = corpus.queries


@then('zapytanie zawiera "{amount}"')
def then_query_holds_amount(context: Context, amount: str) -> None:
    """The amount reaches the evidence search unchanged."""
    assert amount in context.query, context.query


@then(
    "działają tylko wzorce z core/009, a log zapisuje pominięcie bramki DLP"
    " bez treści tekstu"
)
def then_only_patterns_and_skip_logged(context: Context) -> None:
    """The phone is masked, the address stays, the log names the skip only."""
    assert context.masked.text == f"{ADDRESS_TEXT} Dzwoń: [telefon].", (
        context.masked.text
    )
    assert any("skipped" in line for line in context.log_lines), context.log_lines
    assert all("Marszałkowskiej" not in line for line in context.log_lines)
