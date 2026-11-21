"""App database settings from ``MERITUM_DATABASE_*``: which store keeps app data.

Features:
    US-OBS-01, US-MOD-01, US-BEZ-05, F-22, F-24, ADR-04
"""

from enum import StrEnum
from typing import Self

from pydantic import SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from meritum_core.shared.database.constants import ENV_PREFIX


class DatabaseProvider(StrEnum):
    """Which repositories ``build_app_repositories`` builds.

    Features:
        US-OBS-01, F-22, ADR-04
    """

    MEMORY = "memory"
    POSTGRES = "postgres"


class DatabaseSettings(BaseSettings):
    """App database configuration read from ``MERITUM_DATABASE_*`` variables.

    Attributes:
        provider: ``memory`` (default: in-process fakes, tests and runs without a
            database) or ``postgres``.
        url: libpq connection string whose ``search_path`` names the app schema
            (``app_dev`` or ``app_prd``, infra#12); the code never names a schema.

    Features:
        US-OBS-01, US-MOD-01, US-BEZ-05, F-22, F-24, ADR-04
    """

    model_config = SettingsConfigDict(env_prefix=ENV_PREFIX, frozen=True)

    provider: DatabaseProvider = DatabaseProvider.MEMORY
    url: SecretStr | None = None

    @model_validator(mode="after")
    def _postgres_has_a_url(self) -> Self:
        if self.provider is DatabaseProvider.POSTGRES and self.url is None:
            msg = f"{ENV_PREFIX}URL is required for postgres"
            raise ValueError(msg)
        return self
