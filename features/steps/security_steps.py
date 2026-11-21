"""Steps for features/security.feature: they mask text through the public API.

Sensitive Data Protection runs through the factory on a recorded reply (an httpx2
mock transport), so nothing leaves the process.
"""

import asyncio
import logging
from pathlib import Path
from typing import override

import httpx2
from behave import given, then, when
from behave.runner import Context
from google.oauth2.credentials import Credentials

from meritum_core.security import PiiGateSettings, build_pii_gate, mask_personal_data

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


@given("tekst z adresem zamieszkania, którego wzorce z core/009 nie znają")
def given_text_with_address(context: Context) -> None:
    """A street address: no phone, e-mail or PESEL the patterns would catch."""
    context.raw_text = ADDRESS_TEXT


@given("wdrożenie bez konfiguracji DLP")
def given_no_dlp(context: Context) -> None:
    """Default settings, and a text with an address and a phone number."""
    context.raw_text = f"{ADDRESS_TEXT} Dzwoń: 601 234 567."
    context.gate = build_pii_gate(PiiGateSettings())


@when("system maskuje tekst")
def when_system_masks(context: Context) -> None:
    """Mask the remembered text with the configured gate."""
    _mask(context)


@when("system maskuje tekst z włączoną bramką DLP")
def when_system_masks_with_dlp(context: Context) -> None:
    """Mask through Sensitive Data Protection answering with a recorded reply."""
    reply = (FIXTURES / "dlp-address.json").read_bytes()
    transport = httpx2.MockTransport(
        lambda _request: httpx2.Response(200, content=reply)
    )
    settings = PiiGateSettings(gate="sdp", project="meritum-test")
    context.gate = build_pii_gate(
        settings,
        credentials=Credentials(token="recorded"),  # ruff: ignore[hardcoded-password-func-arg]  # fake token, no network
        http_client=httpx2.AsyncClient(transport=transport),
    )
    _mask(context)


@then('wynik zawiera "{phone}", "{email}" i "{pesel}" zamiast tych danych')
def then_markers_replace_data(
    context: Context, phone: str, email: str, pesel: str
) -> None:
    """Every marker is present and no personal data is left."""
    masked = context.masked.text
    assert all(marker in masked for marker in (phone, email, pesel)), masked
    for secret in ("601 234 567", "jan.kowalski@example.pl", "44051401359"):
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


@then("adres jest zastąpiony znacznikiem, a reszta tekstu jest bez zmian")
def then_address_is_masked(context: Context) -> None:
    """The DLP marker stands where the address was; nothing else moved."""
    expected = "Mieszkam przy ul. [adres] i widziałem, że szczepionki zawierają chipy."
    assert context.masked.text == expected, context.masked.text
    assert context.masked.replaced == 1


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
