"""Fixtures for the transcription tests: recordings in a blob store, recorded replies."""

import asyncio
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
    build_transcriber,
)
from meritum_core.shared.blobs import (
    BlobKind,
    BlobSettings,
    BlobStore,
    build_blob_store,
)

FIXTURES = Path(__file__).parent / "fixtures"

type Replies = list[tuple[int, str]]
type Sent = list[httpx2.Request]
type SpeechFactory = Callable[[Replies, int], tuple[TranscriptionPort, Sent]]


@pytest.fixture
def blobs() -> BlobStore:
    return build_blob_store(BlobSettings(provider="memory"))


@pytest.fixture
def audio_id(blobs: BlobStore) -> Callable[[str], str]:
    """Store a fixture recording (or raw bytes for unknown names) and return its id."""

    def store(name: str) -> str:
        path = FIXTURES / name
        data = path.read_bytes() if path.exists() else name.encode()
        expires_at = datetime.now(UTC) + timedelta(hours=1)
        ref = asyncio.run(
            blobs.put(
                data,
                kind=BlobKind.AUDIO,
                content_type="application/octet-stream",
                expires_at=expires_at,
            )
        )
        return ref.blob_id

    return store


@pytest.fixture
def recorded_speech(blobs: BlobStore) -> SpeechFactory:
    """Build Speech-to-Text v2 through the factory; each HTTP call gets the next reply.

    A reply is (status, fixture file name); the last one repeats.
    """

    def build(replies: Replies, retries: int = 1) -> tuple[TranscriptionPort, Sent]:
        sent: Sent = []

        def reply(request: httpx2.Request) -> httpx2.Response:
            status, name = replies[min(len(sent), len(replies) - 1)]
            sent.append(request)
            payload = json.loads((FIXTURES / name).read_text(encoding="utf-8"))
            return httpx2.Response(status, json=payload)

        client = httpx2.AsyncClient(transport=httpx2.MockTransport(reply))
        token = Credentials(token="recorded")  # ruff: ignore[hardcoded-password-func-arg]  # fake token, no network
        settings = TranscriptionSettings(
            provider="speech_v2", project="meritum-test", retries=retries
        )
        speech = build_transcriber(
            settings, blobs, credentials=token, http_client=client
        )
        return speech, sent

    return build
