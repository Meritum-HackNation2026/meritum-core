"""Corpus settings from ``MERITUM_CORPUS_*``: which store answers searches.

Features:
    US-KOR-02, F-12, ADR-04, ADR-32
"""

from enum import StrEnum
from typing import Self

from pydantic import SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from meritum_core.corpus.constants import ENV_PREFIX


class CorpusProvider(StrEnum):
    """Which adapter ``build_corpus_search`` builds.

    Features:
        US-KOR-02, F-12, ADR-04
    """

    MEMORY = "memory"
    POSTGRES = "postgres"


class CorpusSettings(BaseSettings):
    """Corpus search configuration read from ``MERITUM_CORPUS_*`` variables.

    Attributes:
        provider: ``memory`` (default: in-process snapshots, tests and local runs)
            or ``postgres`` (the shared ``corpus`` schema, ADR-32).
        database_url: libpq connection string of the database with the
            ``corpus`` schema; required for postgres.

    Features:
        US-KOR-02, F-12, ADR-04, ADR-32
    """

    model_config = SettingsConfigDict(env_prefix=ENV_PREFIX, frozen=True)

    provider: CorpusProvider = CorpusProvider.MEMORY
    database_url: SecretStr | None = None

    @model_validator(mode="after")
    def _postgres_has_a_database(self) -> Self:
        if self.provider is CorpusProvider.POSTGRES and self.database_url is None:
            msg = f"{ENV_PREFIX}DATABASE_URL is required for postgres"
            raise ValueError(msg)
        return self
