"""Manual check, local only (never in CI): transcribe one real recording.

Answers the open question of ADR-30: does Speech-to-Text v2 decode a Discord
voice message (OGG Opus 48 kHz) without conversion. Needs Application Default
Credentials (``gcloud auth application-default login``) and a project with the
Speech-to-Text API enabled; it sends the file to the ``eu`` multi-region.

    uv run python scripts/transcribe_audio.py voice-message.ogg --project <project>

The recording goes inline to synchronous recognition, so it must be shorter
than ``SYNC_MAX_SECONDS``; the in-memory blob store has no ``gs://`` address
for batch recognition.
"""

import argparse
import asyncio
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

from meritum_core.checks.transcription import (
    TranscriptionError,
    TranscriptionSettings,
    build_transcriber,
    inspect_audio,
)
from meritum_core.shared.blobs import BlobKind, BlobSettings, build_blob_store


async def transcribe(data: bytes, project: str) -> str:
    """Store the file in memory and transcribe it with Speech-to-Text v2.

    Args:
        data: The recording, e.g. a voice message downloaded from Discord.
        project: Google Cloud project billed for the call.

    Returns:
        A report: format, length and the transcript.
    """
    info = inspect_audio(data)
    blobs = build_blob_store(BlobSettings(provider="memory"))
    ref = await blobs.put(
        data,
        kind=BlobKind.AUDIO,
        content_type="application/octet-stream",
        expires_at=datetime.now(UTC) + timedelta(hours=1),
    )
    settings = TranscriptionSettings(provider="speech_v2", project=project)
    transcript = await build_transcriber(settings, blobs).transcribe(ref.blob_id)
    return (
        f"format: {info.format}, length: {info.duration_seconds} s\n"
        f"language: {transcript.language}\ntranscript: {transcript.text}\n"
    )


def main() -> int:
    """Parse the arguments, transcribe, write the report or the error.

    Returns:
        The exit code: 0 on success, 1 when transcription failed.
    """
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("path", type=Path, help="the recording to transcribe")
    parser.add_argument("--project", required=True, help="Google Cloud project")
    args = parser.parse_args()
    try:
        sys.stdout.write(asyncio.run(transcribe(args.path.read_bytes(), args.project)))
    except TranscriptionError as exc:
        sys.stderr.write(f"{type(exc).__name__}: {exc}\n")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
