"""Models of the blob store: what a stored file is and how its id is made.

Features:
    US-SPR-11, US-SPR-08, US-BEZ-05, F-08, ADR-31
"""

import secrets
from enum import StrEnum
from typing import Annotated

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field

from meritum_core.shared.blobs.constants import BLOB_ID_PATTERN


class BlobKind(StrEnum):
    """What a blob holds; its value prefixes the id (``audio_id``, ``image_id``).

    Features:
        US-SPR-11, US-SPR-08, ADR-31
    """

    AUDIO = "audio"
    IMAGE = "image"


class BlobRef(BaseModel):
    """A stored file, as ``BlobStore.put`` returns it.

    Attributes:
        blob_id: the id ``CheckRequest`` carries as ``audio_id`` or ``image_id``.
        kind: what the file holds.
        content_type: the MIME type given on upload, e.g. ``audio/ogg``.
        size: the length in bytes.
        expires_at: when retention removes the file at the latest (ADR-13).

    Features:
        US-SPR-11, US-SPR-08, F-08, ADR-31
    """

    model_config = ConfigDict(frozen=True)

    blob_id: Annotated[str, Field(pattern=BLOB_ID_PATTERN)]
    kind: BlobKind
    content_type: Annotated[str, Field(min_length=1, max_length=255)]
    size: Annotated[int, Field(ge=0)]
    expires_at: AwareDatetime


def new_blob_id(kind: BlobKind) -> str:
    """Make a random blob id that carries no user data.

    Args:
        kind: what the blob holds; it prefixes the id.

    Returns:
        An id matching ``BLOB_ID_PATTERN``.

    Features:
        US-BEZ-05, ADR-31
    """
    return f"{kind}_{secrets.token_hex(16)}"
