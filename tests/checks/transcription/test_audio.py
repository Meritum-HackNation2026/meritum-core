"""inspect_audio: format from the bytes, duration where the container states it, limits."""

from pathlib import Path

import pytest

from meritum_core.checks.transcription import (
    MAX_AUDIO_BYTES,
    MAX_AUDIO_SECONDS,
    AudioFormat,
    UnsupportedAudioError,
    inspect_audio,
)

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.mark.parametrize(
    ("name", "audio_format", "seconds"),
    [
        ("voice-40s.ogg", AudioFormat.OGG_OPUS, 40),
        ("voice-90s.ogg", AudioFormat.OGG_OPUS, 90),
        ("short-2s.wav", AudioFormat.WAV, 2),
        ("short-3s.m4a", AudioFormat.M4A, 3),
    ],
)
def test_format_and_duration_come_from_the_file(
    name: str, audio_format: AudioFormat, seconds: int
) -> None:
    info = inspect_audio((FIXTURES / name).read_bytes())
    assert info.format is audio_format
    assert info.duration_seconds == pytest.approx(seconds, abs=0.1)


def test_mp3_is_supported_with_an_unknown_duration() -> None:
    info = inspect_audio((FIXTURES / "short-3s.mp3").read_bytes())
    assert (info.format, info.duration_seconds) == (AudioFormat.MP3, None)


@pytest.mark.parametrize(
    "data",
    [
        b"",
        b"nagranie.xyz: to nie jest plik audio",
        b"OggS" + bytes(24) + b"\x01vorbis" + bytes(40),  # OGG, but not Opus
        b"RIFF\x00\x00\x00\x00WAVE",  # WAV header cut short
    ],
)
def test_other_files_are_unsupported(data: bytes) -> None:
    with pytest.raises(UnsupportedAudioError):
        inspect_audio(data)


def test_a_file_over_the_size_limit_is_unsupported() -> None:
    wav = (FIXTURES / "short-2s.wav").read_bytes()
    with pytest.raises(UnsupportedAudioError, match="size"):
        inspect_audio(wav + bytes(MAX_AUDIO_BYTES))


def test_a_recording_over_the_length_limit_is_unsupported() -> None:
    ogg = bytearray((FIXTURES / "voice-40s.ogg").read_bytes())
    granule = ogg.rfind(b"OggS") + 6
    too_long = (MAX_AUDIO_SECONDS + 1) * 48_000
    ogg[granule : granule + 8] = too_long.to_bytes(8, "little")
    with pytest.raises(UnsupportedAudioError, match="length"):
        inspect_audio(bytes(ogg))
