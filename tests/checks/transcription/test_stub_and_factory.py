"""build_transcriber picks the adapter from settings; the stub answers from its fixture."""

import asyncio
from collections.abc import Callable
from pathlib import Path

import pytest
from pydantic import ValidationError

from meritum_core.checks.transcription import (
    TranscriptionPort,
    TranscriptionSettings,
    TranscriptionUnavailableError,
    UnsupportedAudioError,
    build_transcriber,
)
from meritum_core.shared.blobs import BlobNotFoundError, BlobStore

FIXTURES = Path(__file__).parent / "fixtures"
STUB_FIXTURE = FIXTURES / "stub-transcript.json"

type StoreAudio = Callable[[str], str]


def test_stub_returns_the_fixture_without_provider_keys(
    blobs: BlobStore, audio_id: StoreAudio, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("MERITUM_TRANSCRIPTION_PROVIDER", "stub")
    monkeypatch.setenv("MERITUM_TRANSCRIPTION_STUB_FIXTURE", str(STUB_FIXTURE))
    stub = build_transcriber(TranscriptionSettings(), blobs)
    transcript = asyncio.run(stub.transcribe(audio_id("voice-40s.ogg")))
    assert (transcript.text, transcript.language) == (
        "Sejm przyjął ustawę o ochronie zwierząt.",
        "pl-PL",
    )


def test_stub_rejects_unsupported_files_like_the_provider(
    blobs: BlobStore, audio_id: StoreAudio
) -> None:
    settings = TranscriptionSettings(stub_fixture=STUB_FIXTURE)
    stub = build_transcriber(settings, blobs)
    with pytest.raises(UnsupportedAudioError):
        asyncio.run(stub.transcribe(audio_id("nagranie.xyz")))


def test_stub_without_a_fixture_fails_as_unavailable(
    blobs: BlobStore, audio_id: StoreAudio
) -> None:
    stub = build_transcriber(TranscriptionSettings(), blobs)
    with pytest.raises(TranscriptionUnavailableError, match="fixture"):
        asyncio.run(stub.transcribe(audio_id("voice-40s.ogg")))


def test_missing_recording_raises_blob_not_found(blobs: BlobStore) -> None:
    stub = build_transcriber(TranscriptionSettings(stub_fixture=STUB_FIXTURE), blobs)
    with pytest.raises(BlobNotFoundError):
        asyncio.run(stub.transcribe("audio_" + "0" * 32))


def test_default_provider_is_the_stub(
    blobs: BlobStore, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("MERITUM_TRANSCRIPTION_PROVIDER", raising=False)
    transcriber = build_transcriber(TranscriptionSettings(), blobs)
    assert type(transcriber).__name__ == "StubTranscriber"


def test_factory_builds_speech_v2_from_settings(blobs: BlobStore) -> None:
    settings = TranscriptionSettings(provider="speech_v2", project="meritum-test")
    transcriber = build_transcriber(settings, blobs)
    assert isinstance(transcriber, TranscriptionPort)
    assert type(transcriber).__name__ == "SpeechV2Transcriber"


def test_speech_v2_needs_a_project() -> None:
    with pytest.raises(ValidationError):
        TranscriptionSettings(provider="speech_v2")


def test_stub_fixture_that_is_not_a_transcript_is_rejected(
    tmp_path: Path, blobs: BlobStore
) -> None:
    path = tmp_path / "bad.json"
    path.write_text('{"text": 3}', encoding="utf-8")
    with pytest.raises(ValidationError):
        build_transcriber(TranscriptionSettings(stub_fixture=path), blobs)
