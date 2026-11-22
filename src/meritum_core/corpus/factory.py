"""Builds the corpus adapters named by ``MERITUM_CORPUS_PROVIDER``.

Features:
    US-KOR-02, F-12, ADR-04, ADR-32
"""

from collections.abc import Mapping, Sequence

from meritum_core.corpus.adapters import (
    MemoryCorpusSearch,
    PostgresCorpusSearch,
    PostgresLegalActMeta,
)
from meritum_core.corpus.fakes import InMemoryLegalActMeta
from meritum_core.corpus.models import Passage
from meritum_core.corpus.ports import CorpusSearchPort, LegalActMetaPort
from meritum_core.corpus.settings import CorpusProvider, CorpusSettings
from meritum_core.shared.embeddings import EmbeddingsPort


def build_corpus_search(
    settings: CorpusSettings,
    embeddings: EmbeddingsPort,
    *,
    snapshots: Mapping[str, Sequence[Passage]] | None = None,
) -> CorpusSearchPort:
    """Build the adapter the settings name.

    Args:
        settings: Usually ``CorpusSettings()`` from the environment.
        embeddings: Embeds the query; must be the model the corpus was indexed with.
        snapshots: Passages per ``corpus_version`` for the memory adapter;
            ignored by postgres.

    Returns:
        The in-memory or the PostgreSQL adapter.

    Raises:
        ValueError: postgres without a database URL (settings built unvalidated).

    Features:
        US-KOR-02, F-12, ADR-04, ADR-32
    """
    match settings.provider:
        case CorpusProvider.POSTGRES:
            if settings.database_url is None:
                msg = "MERITUM_CORPUS_DATABASE_URL is required for postgres"
                raise ValueError(msg)
            conninfo = settings.database_url.get_secret_value()
            return PostgresCorpusSearch(conninfo, embeddings)
        case CorpusProvider.MEMORY:
            return MemoryCorpusSearch(snapshots or {}, embeddings)


def build_legal_act_meta(settings: CorpusSettings) -> LegalActMetaPort:
    """Build the legal act metadata store the settings name.

    Args:
        settings: Usually ``CorpusSettings()`` from the environment.

    Returns:
        The in-memory fake (empty) or the PostgreSQL adapter.

    Raises:
        ValueError: postgres without a database URL (settings built unvalidated).

    Features:
        US-KOR-02, F-12, ADR-04
    """
    match settings.provider:
        case CorpusProvider.POSTGRES:
            if settings.database_url is None:
                msg = "MERITUM_CORPUS_DATABASE_URL is required for postgres"
                raise ValueError(msg)
            return PostgresLegalActMeta(settings.database_url.get_secret_value())
        case CorpusProvider.MEMORY:
            return InMemoryLegalActMeta()
