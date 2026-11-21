"""Constants of transcription: limits, formats and the Speech-to-Text v2 setup.

Features:
    US-SPR-11, F-08, ADR-30
"""

from typing import Final

from pydantic import JsonValue

from meritum_core.checks.transcription.models import AudioFormat

MAX_AUDIO_BYTES: Final = 20 * 1024 * 1024
"""Largest recording accepted, 20 MiB; larger files are unsupported (US-SPR-11)."""

SUPPORTED_FORMATS: Final = frozenset(AudioFormat)
"""Recording formats accepted: OGG with Opus, MP3, M4A (AAC) and WAV (US-SPR-11)."""

MAX_AUDIO_SECONDS: Final = 600
"""Longest recording accepted, 10 minutes; MP3 length is estimated from the bitrate."""

SYNC_MAX_SECONDS: Final = 55
"""Longest recording sent to synchronous recognition; above it (about a minute,
with a margin under the provider's 60 s limit) the batch mode reads ``gs://``."""

SYNC_MAX_BYTES: Final = 10 * 1024 * 1024
"""Largest base64 content sent inline to synchronous recognition (10 MiB)."""

GCS_SCHEME: Final = "gs://"
"""Scheme of the addresses batch recognition reads recordings from."""

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

OPERATION_NAME_PATTERN: Final = r"^projects/[^/]+/locations/[^/]+/operations/[\w-]+$"
"""Name of a long-running operation; only such a path is polled with the token."""

ENV_PREFIX: Final = "MERITUM_TRANSCRIPTION_"
"""Prefix of every transcription setting in the environment."""

OPUS_GRANULE_RATE: Final = 48_000
"""Ogg Opus granule positions count 48 kHz samples, whatever the input rate."""

OGG_MAGIC: Final = b"OggS\x00"
"""Capture pattern and stream version 0 that start every Ogg page."""

OPUS_HEAD: Final = b"OpusHead"
"""First packet of an Ogg Opus stream; it fills the stream's first page."""

OPUS_HEAD_OFFSET: Final = 28
"""Where ``OpusHead`` starts: after the 27-byte page header and one lacing byte."""

OGG_GRANULE_OFFSET: Final = 6
"""Offset of the 64-bit little-endian granule position inside an Ogg page."""

RIFF_MAGIC: Final = b"RIFF"
"""First four bytes of a WAV file."""

WAVE_MAGIC: Final = b"WAVE"
"""RIFF form type of a WAV file, right after ``RIFF`` and the file size."""

RIFF_HEADER_BYTES: Final = 12
"""``RIFF``, the file size and ``WAVE``; the chunks follow."""

WAV_FMT_CHUNK: Final = b"fmt "
"""Id of the WAV chunk describing the samples."""

WAV_BYTE_RATE_OFFSET: Final = 8
"""Offset of the 32-bit byte rate inside the body of the ``fmt `` chunk."""

WAV_DATA_CHUNK: Final = b"data"
"""Id of the WAV chunk holding the samples."""

MP4_FTYP: Final = b"ftyp"
"""Type of the first box of an MP4/M4A file, at offset 4; the major brand follows."""

M4A_BRANDS: Final = frozenset({b"M4A ", b"M4B ", b"mp41", b"mp42", b"isom", b"iso2"})
"""Major brands of MP4 audio files; QuickTime, 3GP and HEIF brands are not audio.

The generic brands (``mp4*``, ``iso*``) also mark video; such a file reaches the
provider and fails as ``technical_failure`` when it holds no audio track."""

MP4_MOVIE: Final = b"moov"
"""Top-level MP4 box holding the movie's metadata."""

MP4_MOVIE_HEADER: Final = b"mvhd"
"""Box inside ``moov`` with the movie's timescale and duration."""

ID3_MAGIC: Final = b"ID3"
"""ID3v2 tag that starts most MP3 files; its 10-byte header ends in a syncsafe size."""

ID3_HEADER_BYTES: Final = 10
"""Length of the ID3v2 header; the tag's size excludes it."""

MP3_FRAME_SYNC: Final = 0xFFE0
"""Eleven set bits that start an MPEG audio frame (first two bytes, masked)."""

MP3_LAYER_III: Final = 0b01
"""Layer bits of an MPEG Layer III (MP3) frame; ADTS AAC has ``00``."""

MP3_VERSION_1: Final = 0b11
"""Version bits of MPEG-1; ``10`` is MPEG-2, ``00`` MPEG-2.5, ``01`` reserved."""

MP3_VERSION_RESERVED: Final = 0b01
"""Reserved MPEG version bits: not an audio frame."""

MP3_V1_KBPS: Final = (0, 32, 40, 48, 56, 64, 80, 96, 112, 128, 160, 192, 224, 256, 320)
"""MPEG-1 Layer III bitrates in kbit/s by bitrate index (0 is free format)."""

MP3_V2_KBPS: Final = (0, 8, 16, 24, 32, 40, 48, 56, 64, 80, 96, 112, 128, 144, 160)
"""MPEG-2 and 2.5 Layer III bitrates in kbit/s by bitrate index."""

HTTP_TIMEOUT_SECONDS: Final = 120.0
"""Timeout of one HTTP call to Speech-to-Text; synchronous recognition of a
minute of audio takes seconds."""

RECOGNITION_CONFIG: Final[dict[str, JsonValue]] = {
    "autoDecodingConfig": {},
    "model": SPEECH_MODEL,
    "languageCodes": [LANGUAGE],
}
"""Speech-to-Text v2 ``RecognitionConfig``: the format is read from the file."""

MP3_HEADER_BYTES: Final = 3
"""Bytes of an MPEG frame header that hold sync, version, layer and bitrate."""

MP3_SAMPLE_RATES: Final = {
    0b11: (44_100, 48_000, 32_000),
    0b10: (22_050, 24_000, 16_000),
    0b00: (11_025, 12_000, 8_000),
}
"""Sample rates in Hz by MPEG version bits (1, 2, 2.5) and sample-rate index."""

MP3_V1_SAMPLES_PER_FRAME: Final = 1152
"""Samples in one MPEG-1 Layer III frame; MPEG-2 and 2.5 frames hold half."""

MP3_VBR_TAGS: Final = (b"Xing", b"Info")
"""Tags of the first frame that states the frame count (VBR and LAME CBR files)."""

MP3_VBR_TAG_SEARCH_BYTES: Final = 40
"""How far after the frame header the Xing/Info tag may start (after side info)."""

MP3_VBR_HAS_FRAMES: Final = 0x1
"""Xing/Info flag: a 32-bit frame count follows the flags."""
