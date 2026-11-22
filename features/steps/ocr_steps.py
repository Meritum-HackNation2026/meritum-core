"""Steps for the OCR scenarios in features/checks.feature.

Cloud Vision runs through the factory on recorded replies (an httpx2 mock
transport), so nothing leaves the process.
"""

import asyncio
from datetime import UTC, date, datetime, timedelta
from pathlib import Path

import httpx2
from behave import given, then, when
from behave.runner import Context
from google.oauth2.credentials import Credentials

from meritum_core.checks.ocr import (
    OcrError,
    OcrSettings,
    OcrUnavailableError,
    build_image_search,
    build_ocr,
)
from meritum_core.shared.blobs import BlobKind, BlobSettings, build_blob_store

FIXTURES = Path(__file__).parents[2] / "tests" / "checks" / "ocr"


def _store(context: Context) -> None:
    context.blobs = build_blob_store(BlobSettings(provider="memory"))
    expires_at = datetime.now(UTC) + timedelta(hours=1)
    ref = asyncio.run(
        context.blobs.put(
            (FIXTURES / "pixel.png").read_bytes(),
            kind=BlobKind.IMAGE,
            content_type="image/png",
            expires_at=expires_at,
        )
    )
    context.image_id = ref.blob_id
    context.reply = (200, "annotate-reply.json")
    context.retries = 2


@given('zrzut ekranu posta z tekstem i datą "{shown}"')
def given_screenshot(context: Context, shown: str) -> None:
    """A screenshot whose recorded OCR reply contains the date ``shown``."""
    assert shown in (FIXTURES / "annotate-reply.json").read_text(encoding="utf-8")
    _store(context)


@given("dostawca OCR zwraca błąd po wyczerpaniu ponowień")
def given_provider_fails(context: Context) -> None:
    """A supported image, but every call answers 503."""
    _store(context)
    context.reply = (503, "unavailable.json")


@given("nie skonfigurowano działającego API ani lokalnej bazy obrazów")
def given_no_image_search(context: Context) -> None:
    """The default image search, with nothing behind it."""
    context.search = build_image_search()


@when("system zleca OCR")
def when_system_runs_ocr(context: Context) -> None:
    """Read through the port built by the factory; keep the error, if any."""
    status, name = context.reply
    payload = (FIXTURES / name).read_bytes()
    context.sent = []

    def reply(request: httpx2.Request) -> httpx2.Response:
        context.sent.append(request)
        return httpx2.Response(status, content=payload)

    settings = OcrSettings(
        provider="vision", project="meritum-test", retries=context.retries
    )
    vision = build_ocr(
        settings,
        context.blobs,
        credentials=Credentials(token="recorded"),  # ruff: ignore[hardcoded-password-func-arg]  # fake token, no network
        http_client=httpx2.AsyncClient(transport=httpx2.MockTransport(reply)),
    )
    context.ocr, context.error = None, None
    try:
        context.ocr = asyncio.run(vision.read(context.image_id))
    except OcrError as exc:
        context.error = exc


@when("system pyta o wcześniejsze wystąpienia")
def when_system_searches(context: Context) -> None:
    """Ask the image search for earlier appearances."""
    context.found = asyncio.run(context.search.search("image_" + "0" * 32))


@then("dostaje odczytany tekst i datę jako kandydata na claim_date")
def then_gets_text_and_date(context: Context) -> None:
    """The result holds the text and the date written in it."""
    assert context.error is None
    assert context.ocr.text.startswith("Pilne!")
    assert context.ocr.claim_date == date(2026, 11, 12)


@then(
    "wynik zaznacza, że data widoczna na obrazie sama nie potwierdza "
    "rzeczywistej daty publikacji"
)
def then_date_is_not_proof(context: Context) -> None:
    """The result says the visible date does not confirm the publication date."""
    assert context.ocr.date_confirms_publication is False


@then('port zwraca jawny wynik "nie wyszukano", który odpowiedź pokazuje użytkownikowi')
def then_not_searched(context: Context) -> None:
    """The search reports that nothing was searched, instead of an empty hit list."""
    assert context.found.searched is False
    assert context.found.occurrences == []


@then('port rzuca udokumentowany błąd, który workflow mapuje na "{status}"')
def then_provider_failure(context: Context, status: str) -> None:
    """The port reports the provider failure, and the error names the check status."""
    assert isinstance(context.error, OcrUnavailableError)
    assert context.error.check_status == status
    assert len(context.sent) == context.retries  # every attempt was made
