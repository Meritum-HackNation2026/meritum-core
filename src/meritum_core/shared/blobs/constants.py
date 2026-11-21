"""Constants of the blob store (ADR-31).

Features:
    US-SPR-11, US-SPR-08, US-BEZ-05, F-08, ADR-31
"""

from typing import Final

BLOB_ID_RANDOM_BYTES: Final = 16
"""Random bytes in a blob id (128 bits), written as 32 hex characters."""

BLOB_ID_PATTERN: Final = rf"^(audio|image)_[0-9a-f]{{{2 * BLOB_ID_RANDOM_BYTES}}}$"
"""A blob id: a ``BlobKind`` value, then random hex; no user data, a safe file name."""

ENV_PREFIX: Final = "MERITUM_BLOB_"
"""Prefix of the environment variables that configure the blob store."""

MEMORY_URI_SCHEME: Final = "memory://"
"""Scheme of the addresses the in-memory fake hands out."""
