"""Steps for the transcription scenarios in features/checks.feature.

Speech-to-Text v2 runs through the factory on recorded replies (an httpx2 mock
transport), so nothing leaves the process.
"""

import asyncio
from datetime import UTC, datetime, timedelta
from pathlib import Path

import httpx2
from behave import given, then, when
from behave.runner import Context
from google.oauth2.credentials import Credentials

from meritum_core.checks.transcription import (
    TranscriptionError,
    TranscriptionSettings,
    TranscriptionUnavailableError,
    UnsupportedAudioError,
    build_transcriber,
)
from meritum_core.shared.blobs import BlobKind, BlobSettings, build_blob_store

FIXTURES = Path(__file__).parents[2] / "tests" / "checks" / "transcription" / "fixtures"


def _store(context: Context, data: bytes) -> None:
    context.blobs = build_blob_store(BlobSettings(provider="memory"))
    expires_at = datetime.now(UTC) + timedelta(hours=1)
    ref = asyncio.run(
        context.blobs.put(
            data, kind=BlobKind.AUDIO, content_type="audio/ogg", expires_at=expires_at
        )
    )
    context.audio_id = ref.blob_id
    context.reply = (200, "recognize-reply.json")
    context.retries = 2


@given("nagranie głosowe OGG z Opus 48 kHz o długości 40 s")
def given_ogg_voice_message(context: Context) -> None:
    """A real 40 s Ogg Opus file, as Discord sends voice messages."""
    _store(context, (FIXTURES / "voice-40s.ogg").read_bytes())


@given('plik "{name}"')
def given_file(context: Context, name: str) -> None:
    """A file that is no recording at all."""
    _store(context, f"{name}: to nie jest nagranie".encode())


@given("Speech-to-Text v2 zwraca błąd po wyczerpaniu ponowień")
def given_provider_fails(context: Context) -> None:
    """A supported recording, but every call answers 503."""
    _store(context, (FIXTURES / "voice-40s.ogg").read_bytes())
    context.reply = (503, "unavailable.json")


@when("system zleca transkrypcję")
def when_system_transcribes(context: Context) -> None:
    """Transcribe through the port built by the factory; keep the error, if any."""
    status, name = context.reply
    payload = (FIXTURES / name).read_bytes()
    context.sent = []

    def reply(request: httpx2.Request) -> httpx2.Response:
        context.sent.append(request)
        return httpx2.Response(status, content=payload)

    transport = httpx2.MockTransport(reply)
    settings = TranscriptionSettings(
        provider="speech_v2", project="meritum-test", retries=context.retries
    )
    speech = build_transcriber(
        settings,
        context.blobs,
        credentials=Credentials(token="recorded"),  # ruff: ignore[hardcoded-password-func-arg]  # fake token, no network
        http_client=httpx2.AsyncClient(transport=transport),
    )
    context.transcript, context.error = None, None
    try:
        context.transcript = asyncio.run(speech.transcribe(context.audio_id))
    except TranscriptionError as exc:
        context.error = exc


@then("dostaje tekst transkrypcji w języku pl-PL")
def then_gets_polish_transcript(context: Context) -> None:
    """The transcript holds the recognised text, in pl-PL."""
    assert context.error is None
    assert context.transcript.text.startswith("Sejm przyjął ustawę")
    assert context.transcript.language == "pl-PL"


@then('port rzuca błąd nieobsługiwanego formatu, który workflow mapuje na "{status}"')
def then_unsupported_format(context: Context, status: str) -> None:
    """The port refuses the file, and the error names the check status."""
    assert isinstance(context.error, UnsupportedAudioError)
    assert context.error.check_status == status


@then('port rzuca błąd dostawcy, który workflow mapuje na "{status}"')
def then_provider_failure(context: Context, status: str) -> None:
    """The port reports the provider failure, and the error names the check status."""
    assert isinstance(context.error, TranscriptionUnavailableError)
    assert context.error.check_status == status
    assert len(context.sent) == context.retries  # every attempt was made
