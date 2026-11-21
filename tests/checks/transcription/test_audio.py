"""inspect_audio: format from the bytes, duration where the container states it, limits."""

from pathlib import Path

import pytest

from meritum_core.checks.transcription import (
    MAX_AUDIO_BYTES,
    MAX_AUDIO_SECONDS,
    AudioFormat,
    AudioTooLongError,
    UnsupportedAudioError,
    UnsupportedAudioFormatError,
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
        ("short-3s-faststart.m4a", AudioFormat.M4A, 3),
    ],
)
def test_format_and_duration_come_from_the_file(
    name: str, audio_format: AudioFormat, seconds: int
) -> None:
    info = inspect_audio((FIXTURES / name).read_bytes())
    assert info.format is audio_format
    assert info.duration_seconds == pytest.approx(seconds, abs=0.1)


def test_wav_chunks_are_found_in_any_order() -> None:
    wav = (FIXTURES / "short-2s.wav").read_bytes()
    junk = b"LIST" + (4).to_bytes(4, "little") + b"INFO"
    info = inspect_audio(wav[:12] + junk + wav[12:])
    assert info.duration_seconds == pytest.approx(2, abs=0.1)


def test_mp3_length_is_estimated_from_the_bitrate() -> None:
    info = inspect_audio((FIXTURES / "short-3s.mp3").read_bytes())
    assert info.format is AudioFormat.MP3
    assert info.duration_seconds == pytest.approx(3, abs=0.5)


def test_ogg_length_comes_from_the_last_page_that_ends_a_packet() -> None:
    ogg = bytearray((FIXTURES / "voice-40s.ogg").read_bytes())
    granule = ogg.rfind(b"OggS") + 6
    ogg[granule : granule + 8] = (-1).to_bytes(8, "little", signed=True)
    assert inspect_audio(bytes(ogg)).duration_seconds == pytest.approx(40, abs=1.5)


@pytest.mark.parametrize(
    "data",
    [
        b"",
        b"nagranie.xyz: to nie jest plik audio",
        b"OggS" + bytes(24) + b"\x01vorbis" + bytes(40),  # OGG, but not Opus
        b"RIFF\x00\x00\x00\x00WAVE",  # WAV header cut short
        (FIXTURES / "short-3s.aac").read_bytes(),  # ADTS AAC: frame sync, no MP3
        (FIXTURES / "short-3s.mov").read_bytes(),  # QuickTime: ftyp, other brand
        b"ID3" + bytes(20),  # ID3 tag with no MPEG audio after it
    ],
)
def test_other_files_are_unsupported(data: bytes) -> None:
    with pytest.raises(UnsupportedAudioFormatError):
        inspect_audio(data)


def test_a_file_over_the_size_limit_is_unsupported() -> None:
    wav = (FIXTURES / "short-2s.wav").read_bytes()
    with pytest.raises(AudioTooLongError, match="size"):
        inspect_audio(wav + bytes(MAX_AUDIO_BYTES))


def test_an_mp3_over_the_length_limit_is_unsupported() -> None:
    mp3 = (FIXTURES / "short-3s.mp3").read_bytes()
    padding = bytes(MAX_AUDIO_SECONDS * 40_000 // 8)  # its first frame states 40 kbit/s
    with pytest.raises(AudioTooLongError, match="length"):
        inspect_audio(mp3 + padding)


def test_a_recording_over_the_length_limit_is_unsupported() -> None:
    ogg = bytearray((FIXTURES / "voice-40s.ogg").read_bytes())
    granule = ogg.rfind(b"OggS") + 6
    too_long = (MAX_AUDIO_SECONDS + 1) * 48_000
    ogg[granule : granule + 8] = too_long.to_bytes(8, "little")
    with pytest.raises(AudioTooLongError, match="length"):
        inspect_audio(bytes(ogg))


@pytest.mark.parametrize("error", [AudioTooLongError, UnsupportedAudioFormatError])
def test_subtypes_keep_the_parent_status(error: type[UnsupportedAudioError]) -> None:
    assert issubclass(error, UnsupportedAudioError)
    assert error.check_status == UnsupportedAudioError.check_status == "out_of_scope"
