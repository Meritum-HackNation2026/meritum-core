"""Builds the corpus search adapter named by ``MERITUM_CORPUS_PROVIDER``.

Features:
    US-KOR-02, F-12, ADR-04, ADR-32
"""

from collections.abc import Mapping, Sequence

from meritum_core.corpus.adapters import MemoryCorpusSearch, PostgresCorpusSearch
from meritum_core.corpus.models import Passage
from meritum_core.corpus.ports import CorpusSearchPort
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

    Features:
        US-KOR-02, F-12, ADR-04, ADR-32
    """
    match settings.provider:
        case CorpusProvider.POSTGRES:
            url = settings.database_url
            conninfo = "" if url is None else url.get_secret_value()
            return PostgresCorpusSearch(conninfo, embeddings)
        case CorpusProvider.MEMORY:
            return MemoryCorpusSearch(snapshots or {}, embeddings)
