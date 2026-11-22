"""The ``MERITUM_CORPUS_READY`` switch of the agent-ready corpus layer.

Features:
    US-KOR-02, F-12
"""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from meritum_core.corpus.ready.constants import READY_FLAG_ENV


class CorpusReadySettings(BaseSettings):
    """Whether searches and the worker use the ``corpus_ready`` layer.

    Attributes:
        enabled: ``MERITUM_CORPUS_READY``; false (default) leaves ingest,
            snapshots, ``search_corpus`` and MCP ``search_sources`` as they were.

    Features:
        US-KOR-02, F-12
    """

    model_config = SettingsConfigDict(frozen=True)

    enabled: bool = Field(default=False, validation_alias=READY_FLAG_ENV)
