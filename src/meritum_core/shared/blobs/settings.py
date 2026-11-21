"""Settings of the blob store, read from ``MERITUM_BLOB_*`` variables.

Features:
    ADR-31
"""

from enum import StrEnum

from pydantic_settings import BaseSettings, SettingsConfigDict

from meritum_core.shared.blobs.constants import ENV_PREFIX


class BlobProvider(StrEnum):
    """The adapter ``build_blob_store`` builds (``MERITUM_BLOB_PROVIDER``).

    Features:
        ADR-31
    """

    MEMORY = "memory"


class BlobSettings(BaseSettings):
    """Blob store configuration; no default provider, so a missing one fails loudly.

    Attributes:
        provider: which adapter to build.

    Features:
        ADR-31
    """

    model_config = SettingsConfigDict(env_prefix=ENV_PREFIX, frozen=True)

    provider: BlobProvider
