"""Settings of the blob store, read from ``MERITUM_BLOB_*`` variables.

Features:
    ADR-31
"""

from enum import StrEnum
from pathlib import Path
from typing import Annotated

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from meritum_core.shared.blobs.constants import ENV_PREFIX


class BlobProvider(StrEnum):
    """The adapter ``build_blob_store`` builds (``MERITUM_BLOB_PROVIDER``).

    Features:
        ADR-31
    """

    MEMORY = "memory"
    FILESYSTEM = "filesystem"
    GCS = "gcs"
    S3 = "s3"


class BlobSettings(BaseSettings):
    """Blob store configuration; no default provider, so a missing one fails loudly.

    Attributes:
        provider: which adapter to build.
        directory: the volume directory of ``filesystem`` (``MERITUM_BLOB_DIRECTORY``).
        bucket: the private bucket of ``gcs`` or ``s3`` (``MERITUM_BLOB_BUCKET``).
        endpoint_url: the S3-compatible service (``MERITUM_BLOB_ENDPOINT_URL``);
            unset means AWS S3.
        region: the S3 region (``MERITUM_BLOB_REGION``); R2 takes ``auto``.

    Features:
        ADR-31
    """

    model_config = SettingsConfigDict(env_prefix=ENV_PREFIX, frozen=True)

    provider: BlobProvider
    directory: Path | None = None
    bucket: Annotated[str, Field(min_length=1)] | None = None
    endpoint_url: Annotated[str, Field(min_length=1)] | None = None
    region: Annotated[str, Field(min_length=1)] | None = None
