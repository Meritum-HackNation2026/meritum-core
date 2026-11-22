"""The corpus search port, called in process by research agents and ``search_sources``.

Features:
    US-KOR-02, US-ZRD-05, F-12, ADR-19, ADR-32
"""

from collections.abc import Sequence
from datetime import date
from typing import Protocol, runtime_checkable

from meritum_core.corpus.constants import DEFAULT_LIMIT
from meritum_core.corpus.models import LegalActMeta, Passage


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
            Passages with source id, dates and fused score. The vector ranking
            always yields nearest neighbours, so only an empty snapshot gives
            an empty list.

        Raises:
            ValueError: ``limit`` is below 1.
            UnknownCorpusVersionError: No snapshot has this version.
            CorpusUnavailableError: The corpus store failed.
            EmbeddingsUnavailableError: The query could not be embedded.
        """
        ...


@runtime_checkable
class LegalActMetaPort(Protocol):
    """Legal act metadata of corpus documents, one record per ``source_id``.

    Internal to the corpus: the worker's ingestion writes it, ``corpus_ready``
    and the evidence steps read it. Not part of the checks contract.

    Features:
        US-KOR-02, US-ZRD-05, F-12
    """

    async def save(self, source_id: str, meta: LegalActMeta) -> None:
        """Store the act's metadata, replacing what the document had.

        Args:
            source_id: The ``corpus.documents`` row the act was ingested as.
            meta: What ELI says about the act.

        Raises:
            CorpusUnavailableError: The corpus store failed, or no document
                has this ``source_id``.
        """
        ...

    async def read(self, source_ids: Sequence[str]) -> dict[str, LegalActMeta]:
        """Return the metadata of those documents that are legal acts.

        Args:
            source_ids: Documents to look up.

        Returns:
            Metadata per ``source_id``; a document outside ELI is missing.

        Raises:
            CorpusUnavailableError: The corpus store failed.
        """
        ...
