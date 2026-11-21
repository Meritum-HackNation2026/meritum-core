"""The corpus search port, called in process by research agents and ``search_sources``.

Features:
    US-KOR-02, US-ZRD-05, F-12, ADR-19, ADR-32
"""

from datetime import date
from typing import Protocol, runtime_checkable

from meritum_core.corpus.constants import DEFAULT_LIMIT
from meritum_core.corpus.models import Passage


@runtime_checkable
class CorpusSearchPort(Protocol):
    """Hybrid search of one pinned corpus snapshot, fresher passages preferred.

    Features:
        US-KOR-02, US-ZRD-05, F-12, ADR-04, ADR-19, ADR-32
    """

    async def search(
        self,
        query: str,
        *,
        claim_date: date,
        corpus_version: str,
        limit: int = DEFAULT_LIMIT,
    ) -> list[Passage]:
        """Return the best passages for ``query``, best first.

        Args:
            query: The claim or a researcher's question, already masked.
            claim_date: The date the claim is about; passage age counts from it.
            corpus_version: The snapshot pinned for this check (ADR-19).
            limit: Most passages to return.

        Returns:
            Passages with source id, dates and fused score; empty when none match.

        Raises:
            UnknownCorpusVersionError: No snapshot has this version.
            CorpusUnavailableError: The corpus store failed.
            EmbeddingsUnavailableError: The query could not be embedded.
        """
        ...
