"""Recognise a recording's format and length from its bytes, without decoding it.

The upload's MIME type comes from the user, so the bytes decide. Adapters call
``inspect_audio`` before anything leaves the process.

Features:
    US-SPR-11, F-08, ADR-30
"""

from collections.abc import Iterator

from meritum_core.checks.transcription.constants import (
    ID3_HEADER_BYTES,
    ID3_MAGIC,
    M4A_BRANDS,
    MAX_AUDIO_BYTES,
    MAX_AUDIO_SECONDS,
    MP3_FRAME_SYNC,
    MP3_HEADER_BYTES,
    MP3_LAYER_III,
    MP3_SAMPLE_RATES,
    MP3_V1_KBPS,
    MP3_V1_SAMPLES_PER_FRAME,
    MP3_V2_KBPS,
    MP3_VBR_HAS_FRAMES,
    MP3_VBR_TAG_SEARCH_BYTES,
    MP3_VBR_TAGS,
    MP3_VERSION_1,
    MP3_VERSION_RESERVED,
    MP4_FTYP,
    MP4_MOVIE,
    MP4_MOVIE_HEADER,
    OGG_GRANULE_OFFSET,
    OGG_MAGIC,
    OPUS_GRANULE_RATE,
    OPUS_HEAD,
    OPUS_HEAD_OFFSET,
    RIFF_HEADER_BYTES,
    RIFF_MAGIC,
    SUPPORTED_FORMATS,
    WAV_BYTE_RATE_OFFSET,
    WAV_DATA_CHUNK,
    WAV_FMT_CHUNK,
    WAVE_MAGIC,
)
from meritum_core.checks.transcription.errors import (
    AudioTooLongError,
    UnsupportedAudioFormatError,
)
from meritum_core.checks.transcription.models import AudioFormat, AudioInfo


def inspect_audio(data: bytes) -> AudioInfo:
    """Return the recording's format and length, or reject it.

    Args:
        data: The whole file.

    Returns:
        The format and the length the container states (estimated from the
        bitrate for MP3).

    Raises:
        UnsupportedAudioFormatError: Not OGG Opus, MP3, M4A or WAV, or no
            readable length.
        AudioTooLongError: Over ``MAX_AUDIO_BYTES`` / ``MAX_AUDIO_SECONDS``.

    Features:
        US-SPR-11, F-08, ADR-30
    """
    if len(data) > MAX_AUDIO_BYTES:
        msg = f"recording size {len(data)} B is over {MAX_AUDIO_BYTES} B"
        raise AudioTooLongError(msg)
    audio_format, seconds = _probe(data)
    if audio_format is None or seconds is None:
        formats = ", ".join(sorted(SUPPORTED_FORMATS))
        msg = f"recording is not one of {formats} with a readable length"
        raise UnsupportedAudioFormatError(msg)
    if seconds > MAX_AUDIO_SECONDS:
        msg = f"recording length {seconds:.0f} s is over {MAX_AUDIO_SECONDS} s"
        raise AudioTooLongError(msg)
    return AudioInfo(format=audio_format, duration_seconds=seconds)


def _probe(data: bytes) -> tuple[AudioFormat | None, float | None]:
    if _is_ogg_opus(data):
        return AudioFormat.OGG_OPUS, _ogg_seconds(data)
    if data.startswith(RIFF_MAGIC) and data[8:RIFF_HEADER_BYTES] == WAVE_MAGIC:
        return AudioFormat.WAV, _wav_seconds(data)
    if data[4:8] == MP4_FTYP and data[8:12] in M4A_BRANDS:
        return AudioFormat.M4A, _m4a_seconds(data)
    frame = _id3_size(data)
    bitrate = _mp3_bitrate(data[frame : frame + MP3_HEADER_BYTES])
    if bitrate is not None:
        # The larger of the frame count and the size: a tag cannot hide extra bytes.
        by_size = (len(data) - frame) * 8 / bitrate
        return AudioFormat.MP3, max(_mp3_tagged_seconds(data, frame), by_size)
    return None, None


def _number(data: bytes, at: int, width: int, *, little: bool = False) -> int:
    return int.from_bytes(data[at : at + width], "little" if little else "big")


def _is_ogg_opus(data: bytes) -> bool:
    head = data[OPUS_HEAD_OFFSET : OPUS_HEAD_OFFSET + len(OPUS_HEAD)]
    return data.startswith(OGG_MAGIC) and head == OPUS_HEAD


def _ogg_seconds(data: bytes) -> float | None:
    # The last page that ends a packet holds the stream's length; granule -1
    # marks a page on which no packet ends.
    page = data.rfind(OGG_MAGIC)
    while page > 0:
        at = page + OGG_GRANULE_OFFSET
        granule = int.from_bytes(data[at : at + 8], "little", signed=True)
        if granule > 0:
            return granule / OPUS_GRANULE_RATE
        page = data.rfind(OGG_MAGIC, 0, page)
    return None


def _wav_seconds(data: bytes) -> float | None:
    byte_rate, size = 0, None
    at = RIFF_HEADER_BYTES
    while at + 8 <= len(data):
        chunk, length = data[at : at + 4], _number(data, at + 4, 4, little=True)
        if chunk == WAV_FMT_CHUNK:
            byte_rate = _number(data, at + 8 + WAV_BYTE_RATE_OFFSET, 4, little=True)
        elif chunk == WAV_DATA_CHUNK:
            size = min(length, len(data) - at - 8)  # streamed WAVs state 0xFFFFFFFF
        at += 8 + length + length % 2
    return size / byte_rate if byte_rate and size is not None else None


def _boxes(data: bytes, start: int, end: int) -> Iterator[tuple[bytes, int, int]]:
    """Yield (type, body start, end) of the MP4 boxes between start and end."""
    at = start
    while at + 8 <= end:
        size, header = _number(data, at, 4), 8
        if size == 1:  # 64-bit size after the type
            size, header = _number(data, at + 8, 8), 16
        elif size == 0:  # the box runs to the end
            size = end - at
        if size < header:
            return
        yield data[at + 4 : at + 8], at + header, min(at + size, end)
        at += size


def _box(data: bytes, kind: bytes, start: int, end: int) -> tuple[int, int] | None:
    return next(((b, e) for t, b, e in _boxes(data, start, end) if t == kind), None)


def _m4a_seconds(data: bytes) -> float | None:
    moov = _box(data, MP4_MOVIE, 0, len(data))
    mvhd = None if moov is None else _box(data, MP4_MOVIE_HEADER, *moov)
    if mvhd is None:
        return None
    body, end = mvhd
    # After version and 3 flag bytes: creation and modification times of 4 (v0)
    # or 8 (v1) bytes, the 32-bit timescale, then the duration of the same width.
    width = 8 if data[body : body + 1] == b"\x01" else 4
    timescale_at = body + 4 + 2 * width
    if timescale_at + 4 + width > end:
        return None
    timescale = _number(data, timescale_at, 4)
    duration = _number(data, timescale_at + 4, width)
    return duration / timescale if timescale else None


def _id3_size(data: bytes) -> int:
    if not data.startswith(ID3_MAGIC) or len(data) < ID3_HEADER_BYTES:
        return 0
    size = 0
    for byte in data[6:ID3_HEADER_BYTES]:  # syncsafe: 7 bits per byte
        size = size << 7 | byte & 0x7F
    return ID3_HEADER_BYTES + size


def _mp3_bitrate(header: bytes) -> int | None:
    # Bits per second of an MPEG Layer III frame header, None for anything else.
    if len(header) < MP3_HEADER_BYTES:
        return None
    has_sync = _number(header, 0, 2) & MP3_FRAME_SYNC == MP3_FRAME_SYNC
    version = header[1] >> 3 & 0b11
    is_layer_iii = header[1] >> 1 & 0b11 == MP3_LAYER_III
    index = header[2] >> 4
    table = MP3_V1_KBPS if version == MP3_VERSION_1 else MP3_V2_KBPS
    is_valid_version = version != MP3_VERSION_RESERVED
    if not (has_sync and is_layer_iii and is_valid_version and 0 < index < len(table)):
        return None
    return table[index] * 1000


def _mp3_tagged_seconds(data: bytes, frame: int) -> float:
    # Exact length from a Xing/Info frame count; 0 for untagged (CBR) files.
    window = data[frame : frame + MP3_HEADER_BYTES + 1 + MP3_VBR_TAG_SEARCH_BYTES]
    tag = max(window.find(t) for t in MP3_VBR_TAGS)
    if tag < 0 or not _number(window, tag + 4, 4) & MP3_VBR_HAS_FRAMES:
        return 0
    frames = _number(data, frame + tag + 8, 4)
    version, rate_index = data[frame + 1] >> 3 & 0b11, data[frame + 2] >> 2 & 0b11
    rates = MP3_SAMPLE_RATES.get(version, ())
    if rate_index >= len(rates):
        return 0
    per_frame = MP3_V1_SAMPLES_PER_FRAME // (1 if version == MP3_VERSION_1 else 2)
    return frames * per_frame / rates[rate_index]
