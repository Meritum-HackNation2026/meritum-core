"""Constants of transcription: limits, formats and the Speech-to-Text v2 setup.

Features:
    US-SPR-11, F-08, ADR-30
"""

from typing import Final

from pydantic import JsonValue

MAX_AUDIO_BYTES: Final = 20 * 1024 * 1024
"""Largest recording accepted, 20 MiB; larger files are unsupported (US-SPR-11)."""

MAX_AUDIO_SECONDS: Final = 600
"""Longest recording accepted, 10 minutes; checked where the container states it."""

SYNC_MAX_SECONDS: Final = 55
"""Longest recording sent to synchronous recognition; above it (about a minute,
with a margin under the provider's 60 s limit) the batch mode reads ``gs://``."""

SYNC_MAX_BYTES: Final = 10 * 1024 * 1024
"""Largest inline content of synchronous recognition (provider limit, 10 MiB)."""

LANGUAGE: Final = "pl-PL"
"""Language every recording is transcribed in; GA for Chirp 3 in ``eu`` (ADR-30)."""

SPEECH_MODEL: Final = "chirp_3"
"""Speech-to-Text v2 model (ADR-30)."""

SPEECH_LOCATION: Final = "eu"
"""Speech-to-Text v2 multi-region; the audio is processed in the EU (ADR-14, ADR-30)."""

SPEECH_ENDPOINT: Final = "https://eu-speech.googleapis.com/v2"
"""Regional REST endpoint serving the ``eu`` location."""

SPEECH_SCOPES: Final = ("https://www.googleapis.com/auth/cloud-platform",)
"""OAuth scopes the adapter asks Application Default Credentials for."""

DEFAULT_RETRIES: Final = 3
"""HTTP attempts per call, the first included, before TranscriptionUnavailableError."""

RETRY_BACKOFF_SECONDS: Final = 0.5
"""Pause before the second attempt; it doubles for every next one."""

BATCH_POLL_SECONDS: Final = 2.0
"""Pause between reads of a running batch operation."""

BATCH_TIMEOUT_SECONDS: Final = 900.0
"""Longest wait for a batch operation before the provider counts as failed."""

ENV_PREFIX: Final = "MERITUM_TRANSCRIPTION_"
"""Prefix of every transcription setting in the environment."""

OPUS_GRANULE_RATE: Final = 48_000
"""Ogg Opus granule positions count 48 kHz samples, whatever the input rate."""

OGG_MAGIC: Final = b"OggS"
"""Capture pattern that starts every Ogg page."""

OPUS_HEAD: Final = b"OpusHead"
"""First packet of an Ogg Opus stream; it fills the stream's first page."""

OPUS_HEAD_OFFSET: Final = 28
"""Where ``OpusHead`` starts: after the 27-byte page header and one lacing byte."""

OGG_GRANULE_OFFSET: Final = 6
"""Offset of the 64-bit little-endian granule position inside an Ogg page."""

RIFF_MAGIC: Final = b"RIFF"
"""First four bytes of a WAV file."""

WAVE_MAGIC: Final = b"WAVE"
"""RIFF form type of a WAV file, at offset 8."""

WAV_BYTE_RATE_OFFSET: Final = 28
"""Offset of the 32-bit byte rate in the canonical ``fmt `` chunk of a WAV file."""

WAV_DATA_CHUNK: Final = b"data"
"""Id of the WAV chunk holding the samples; its 32-bit size follows it."""

MP4_FTYP: Final = b"ftyp"
"""Type of the first box of an MP4/M4A file, at offset 4."""

MP4_MOVIE_HEADER: Final = b"mvhd"
"""Box with the movie's timescale and duration."""

MP3_ID3_TAG: Final = b"ID3"
"""ID3v2 tag that starts most MP3 files."""

MP3_FRAME_SYNC: Final = 0xFFE0
"""Eleven set bits that start an MPEG audio frame (first two bytes, masked)."""

HTTP_TIMEOUT_SECONDS: Final = 120.0
"""Timeout of one HTTP call to Speech-to-Text; synchronous recognition of a
minute of audio takes seconds."""

RECOGNITION_CONFIG: Final[dict[str, JsonValue]] = {
    "autoDecodingConfig": {},
    "model": SPEECH_MODEL,
    "languageCodes": [LANGUAGE],
}
"""Speech-to-Text v2 ``RecognitionConfig``: the format is read from the file."""
