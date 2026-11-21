"""Speech-to-Text v2 adapter on recorded replies: no network."""

import asyncio
import base64
import json
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from pathlib import Path

import httpx2
import pytest
from google.oauth2.credentials import Credentials

from meritum_core.checks.transcription import (
    TranscriptionPort,
    TranscriptionSettings,
    TranscriptionUnavailableError,
    UnsupportedAudioError,
    build_transcriber,
)
from meritum_core.shared.blobs import (
    BlobKind,
    BlobSettings,
    BlobStore,
    build_blob_store,
)

FIXTURES = Path(__file__).parent / "fixtures"

RECOGNIZER = (
    "https://eu-speech.googleapis.com/v2/projects/meritum-test/locations/eu"
    "/recognizers/_"
)
OPERATION = (
    "https://eu-speech.googleapis.com/v2/projects/meritum-test/locations/eu"
    "/operations/42"
)
CONFIG = {"autoDecodingConfig": {}, "model": "chirp_3", "languageCodes": ["pl-PL"]}

type Replies = list[tuple[int, str]]
type SpeechFactory = Callable[..., tuple[TranscriptionPort, list[httpx2.Request]]]
type StoreAudio = Callable[[str], str]


def test_short_recording_goes_inline_to_synchronous_recognition(
    recorded_speech: SpeechFactory, audio_id: StoreAudio, blobs: BlobStore
) -> None:
    speech, sent = recorded_speech([(200, "recognize-reply.json")])
    voice = audio_id("voice-40s.ogg")
    transcript = asyncio.run(speech.transcribe(voice))
    assert transcript.text == (
        "Sejm przyjął ustawę o ochronie zwierząt. Weszła w życie w maju."
    )
    assert transcript.language == "pl-PL"
    [request] = sent
    assert str(request.url) == f"{RECOGNIZER}:recognize"
    assert request.headers["authorization"] == "Bearer recorded"
    sent_body = json.loads(request.content)
    assert sent_body["config"] == CONFIG
    stored = asyncio.run(blobs.get(voice))
    assert base64.b64decode(sent_body["content"]) == stored


def test_long_recording_goes_to_batch_from_the_store_address(
    recorded_speech: SpeechFactory, audio_id: StoreAudio, blobs: BlobStore
) -> None:
    replies = [
        (200, "batch-running.json"),
        (200, "batch-done.json"),
    ]
    speech, sent = recorded_speech(replies)
    voice = audio_id("voice-90s.ogg")
    transcript = asyncio.run(speech.transcribe(voice))
    assert transcript.text == "Rząd obniżył VAT na żywność."
    start, poll = sent
    assert str(start.url) == f"{RECOGNIZER}:batchRecognize"
    assert json.loads(start.content) == {
        "config": CONFIG,
        "files": [{"uri": asyncio.run(blobs.uri(voice))}],
        "recognitionOutputConfig": {"inlineResponseConfig": {}},
    }
    assert (poll.method, str(poll.url)) == ("GET", OPERATION)


def test_batch_needs_a_gs_address_from_the_store() -> None:
    memory = build_blob_store(BlobSettings(provider="memory"))
    voice = asyncio.run(
        memory.put(
            (FIXTURES / "voice-90s.ogg").read_bytes(),
            kind=BlobKind.AUDIO,
            content_type="audio/ogg",
            expires_at=datetime.now(UTC) + timedelta(hours=1),
        )
    )
    settings = TranscriptionSettings(provider="speech_v2", project="meritum-test")
    sent: list[httpx2.Request] = []
    client = httpx2.AsyncClient(
        transport=httpx2.MockTransport(lambda r: sent.append(r) or httpx2.Response(500))
    )
    token = Credentials(token="recorded")  # ruff: ignore[hardcoded-password-func-arg]  # fake token, no network
    speech = build_transcriber(settings, memory, credentials=token, http_client=client)
    with pytest.raises(TranscriptionUnavailableError, match="gs://"):
        asyncio.run(speech.transcribe(voice.blob_id))
    assert sent == []


def test_unsupported_file_fails_before_anything_is_sent(
    recorded_speech: SpeechFactory, audio_id: StoreAudio
) -> None:
    speech, sent = recorded_speech([(200, "recognize-reply.json")])
    with pytest.raises(UnsupportedAudioError):
        asyncio.run(speech.transcribe(audio_id("nagranie.xyz")))
    assert sent == []


def test_provider_failure_after_retries_raises_unavailable(
    recorded_speech: SpeechFactory, audio_id: StoreAudio
) -> None:
    speech, sent = recorded_speech([(503, "unavailable.json")], 2)
    with pytest.raises(TranscriptionUnavailableError):
        asyncio.run(speech.transcribe(audio_id("voice-40s.ogg")))
    assert len(sent) == 2


def test_transient_failure_is_retried(
    recorded_speech: SpeechFactory, audio_id: StoreAudio
) -> None:
    replies = [(503, "unavailable.json"), (200, "recognize-reply.json")]
    speech, sent = recorded_speech(replies, 2)
    transcript = asyncio.run(speech.transcribe(audio_id("voice-40s.ogg")))
    assert transcript.text.startswith("Sejm")
    assert len(sent) == 2


def test_rejected_request_is_not_retried(
    recorded_speech: SpeechFactory, audio_id: StoreAudio
) -> None:
    speech, sent = recorded_speech([(400, "invalid-argument.json")], 3)
    with pytest.raises(TranscriptionUnavailableError):
        asyncio.run(speech.transcribe(audio_id("voice-40s.ogg")))
    assert len(sent) == 1


def test_batch_file_error_raises_unavailable(
    recorded_speech: SpeechFactory, audio_id: StoreAudio
) -> None:
    speech, _ = recorded_speech([(200, "batch-file-error.json")])
    with pytest.raises(TranscriptionUnavailableError):
        asyncio.run(speech.transcribe(audio_id("voice-90s.ogg")))


def test_rejected_credentials_raise_unavailable(
    blobs: BlobStore, audio_id: StoreAudio
) -> None:
    settings = TranscriptionSettings(provider="speech_v2", project="meritum-test")
    expired = Credentials(token=None)  # cannot refresh: no refresh token
    speech = build_transcriber(settings, blobs, credentials=expired)
    with pytest.raises(TranscriptionUnavailableError):
        asyncio.run(speech.transcribe(audio_id("voice-40s.ogg")))


def test_operation_with_an_unexpected_name_is_not_polled(
    recorded_speech: SpeechFactory, audio_id: StoreAudio
) -> None:
    speech, sent = recorded_speech([(200, "batch-bad-name.json")])
    with pytest.raises(TranscriptionUnavailableError):
        asyncio.run(speech.transcribe(audio_id("voice-90s.ogg")))
    assert len(sent) == 1
