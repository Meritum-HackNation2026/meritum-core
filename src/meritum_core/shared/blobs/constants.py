"""Constants of the blob store (ADR-31).

Features:
    US-SPR-11, US-SPR-08, US-BEZ-05, F-08, ADR-31
"""

from typing import Final

BLOB_ID_RANDOM_BYTES: Final = 16
"""Random bytes in a blob id (128 bits), written as 32 hex characters."""

BLOB_ID_PATTERN: Final = (
    rf"^(audio|image|dataset)_[0-9a-f]{{{2 * BLOB_ID_RANDOM_BYTES}}}$"
)
"""A blob id: a ``BlobKind`` value, then random hex; no user data, a safe file name."""

ENV_PREFIX: Final = "MERITUM_BLOB_"
"""Prefix of the environment variables that configure the blob store."""

MEMORY_URI_SCHEME: Final = "memory://"
"""Scheme of the addresses the in-memory fake hands out."""

GCS_URI_SCHEME: Final = "gs://"
"""Scheme of Cloud Storage addresses, read by Speech-to-Text batch (ADR-30)."""

S3_URI_SCHEME: Final = "s3://"
"""Scheme of addresses on an S3-compatible bucket."""

S3_MISSING_CODES: Final = frozenset({"404", "NoSuchKey", "NotFound"})
"""Error codes with which an S3 service says an object does not exist."""

PARTIAL_SUFFIX: Final = ".part"
"""Suffix of a file the filesystem adapter is still writing; renamed when complete."""
