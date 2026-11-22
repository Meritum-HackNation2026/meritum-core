"""In-memory legal act metadata: the fake for tests and runs without a database.

Features:
    US-KOR-02, F-12
"""

from collections.abc import Sequence

from meritum_core.corpus.models import LegalActMeta


class InMemoryLegalActMeta:
    """LegalActMetaPort over a dict; it does not check that the document exists.

    Features:
        US-KOR-02, F-12
    """

    def __init__(self) -> None:
        self._rows: dict[str, LegalActMeta] = {}

    async def save(self, source_id: str, meta: LegalActMeta) -> None:
        """Store the act's metadata (see ``LegalActMetaPort.save``).

        Args:
            source_id: The document.
            meta: The act's metadata.
        """
        self._rows[source_id] = meta

    async def read(self, source_ids: Sequence[str]) -> dict[str, LegalActMeta]:
        """Return the stored metadata (see ``LegalActMetaPort.read``).

        Args:
            source_ids: Documents to look up.

        Returns:
            Metadata per ``source_id`` of the legal acts among them.
        """
        return {s: self._rows[s] for s in source_ids if s in self._rows}
