"""Constants of the blob store (ADR-31).

Features:
    US-SPR-11, US-SPR-08, US-BEZ-05, F-08, ADR-31
"""

from typing import Final

BLOB_ID_PATTERN: Final = r"^(audio|image)_[0-9a-f]{32}$"
"""A blob id: its kind, then 128 random bits as hex; no user data, a safe file name."""

ENV_PREFIX: Final = "MERITUM_BLOB_"
"""Prefix of the environment variables that configure the blob store."""

MEMORY_URI_SCHEME: Final = "memory://"
"""Scheme of the addresses the in-memory fake hands out."""
