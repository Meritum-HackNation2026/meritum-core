"""Models of transcription: what a recording is and what the port returns.

Features:
    US-SPR-11, F-08, ADR-30
"""

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class AudioFormat(StrEnum):
    """Recording formats the port accepts, recognised from the file's bytes.

    Features:
        US-SPR-11, F-08, ADR-30
    """

    OGG_OPUS = "ogg_opus"
    MP3 = "mp3"
    M4A = "m4a"
    WAV = "wav"


class AudioInfo(BaseModel):
    """What ``inspect_audio`` learnt from a recording without decoding it.

    Attributes:
        format: The container and codec.
        duration_seconds: Length stated by the container; None when it does not
            state one cheaply (MP3).

    Features:
        US-SPR-11, F-08
    """

    model_config = ConfigDict(frozen=True)

    format: AudioFormat
    duration_seconds: float | None = Field(default=None, ge=0)


class Transcript(BaseModel):
    """Text of a recording, checked like any other text afterwards.

    Attributes:
        text: The transcript; empty when the recording holds no speech.
        language: BCP-47 code of the transcript's language, e.g. ``pl-PL``.

    Features:
        US-SPR-11, F-08, ADR-30
    """

    model_config = ConfigDict(frozen=True)

    text: str
    language: str = Field(min_length=2)
