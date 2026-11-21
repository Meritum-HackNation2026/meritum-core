"""Recognise a recording's format and length from its bytes, without decoding it.

The upload's MIME type comes from the user, so the bytes decide. Adapters call
``inspect_audio`` before anything leaves the process.

Features:
    US-SPR-11, F-08, ADR-30
"""

from meritum_core.checks.transcription.constants import (
    MAX_AUDIO_BYTES,
    MAX_AUDIO_SECONDS,
    MP3_FRAME_SYNC,
    MP3_ID3_TAG,
    MP4_FTYP,
    MP4_MOVIE_HEADER,
    OGG_GRANULE_OFFSET,
    OGG_MAGIC,
    OPUS_GRANULE_RATE,
    OPUS_HEAD,
    OPUS_HEAD_OFFSET,
    RIFF_MAGIC,
    WAV_BYTE_RATE_OFFSET,
    WAV_DATA_CHUNK,
    WAVE_MAGIC,
)
from meritum_core.checks.transcription.errors import UnsupportedAudioError
from meritum_core.checks.transcription.models import AudioFormat, AudioInfo


def inspect_audio(data: bytes) -> AudioInfo:
    """Return the recording's format and length, or reject it.

    Args:
        data: The whole file.

    Returns:
        The format and, where the container states it, the length.

    Raises:
        UnsupportedAudioError: Not OGG Opus, MP3, M4A or WAV, a truncated
            header, or over ``MAX_AUDIO_BYTES`` / ``MAX_AUDIO_SECONDS``.

    Features:
        US-SPR-11, F-08, ADR-30
    """
    if len(data) > MAX_AUDIO_BYTES:
        msg = f"recording size {len(data)} B is over {MAX_AUDIO_BYTES} B"
        raise UnsupportedAudioError(msg)
    info = _probe(data)
    if info is None:
        msg = "recording is not OGG Opus, MP3, M4A or WAV"
        raise UnsupportedAudioError(msg)
    seconds = info.duration_seconds
    if seconds is not None and seconds > MAX_AUDIO_SECONDS:
        msg = f"recording length {seconds:.0f} s is over {MAX_AUDIO_SECONDS} s"
        raise UnsupportedAudioError(msg)
    return info


def _probe(data: bytes) -> AudioInfo | None:
    if _is_ogg_opus(data):
        return AudioInfo(
            format=AudioFormat.OGG_OPUS, duration_seconds=_ogg_seconds(data)
        )
    if _is_wav(data):
        return AudioInfo(format=AudioFormat.WAV, duration_seconds=_wav_seconds(data))
    if data[4:8] == MP4_FTYP:
        return AudioInfo(format=AudioFormat.M4A, duration_seconds=_m4a_seconds(data))
    if _is_mp3(data):
        return AudioInfo(format=AudioFormat.MP3)
    return None


def _number(data: bytes, at: int, width: int, *, little: bool = False) -> int:
    return int.from_bytes(data[at : at + width], "little" if little else "big")


def _is_ogg_opus(data: bytes) -> bool:
    head = data[OPUS_HEAD_OFFSET : OPUS_HEAD_OFFSET + len(OPUS_HEAD)]
    return data.startswith(OGG_MAGIC) and head == OPUS_HEAD


def _ogg_seconds(data: bytes) -> float:
    at = data.rfind(OGG_MAGIC) + OGG_GRANULE_OFFSET
    granule = int.from_bytes(data[at : at + 8], "little", signed=True)
    return max(granule, 0) / OPUS_GRANULE_RATE  # -1: no packet ends on the page


def _is_wav(data: bytes) -> bool:
    has_header = len(data) >= WAV_BYTE_RATE_OFFSET + 4
    return has_header and data.startswith(RIFF_MAGIC) and data[8:12] == WAVE_MAGIC


def _wav_seconds(data: bytes) -> float | None:
    byte_rate = _number(data, WAV_BYTE_RATE_OFFSET, 4, little=True)
    chunk = data.find(WAV_DATA_CHUNK, 12)
    if byte_rate == 0 or chunk < 0 or chunk + 8 > len(data):
        return None
    return _number(data, chunk + 4, 4, little=True) / byte_rate


def _m4a_seconds(data: bytes) -> float | None:
    box = data.find(MP4_MOVIE_HEADER)
    # After version and 3 flag bytes: creation and modification times of 4 (v0)
    # or 8 (v1) bytes, the 32-bit timescale, then the duration of the same width.
    width = 8 if data[box + 4 : box + 5] == b"\x01" else 4
    timescale_at = box + 8 + 2 * width
    if box < 0 or timescale_at + 4 + width > len(data):
        return None
    timescale = _number(data, timescale_at, 4)
    duration = _number(data, timescale_at + 4, width)
    return duration / timescale if timescale else None


def _is_mp3(data: bytes) -> bool:
    has_frame = len(data) > 1 and _number(data, 0, 2) & MP3_FRAME_SYNC == MP3_FRAME_SYNC
    return data.startswith(MP3_ID3_TAG) or has_frame
