"""Legal act metadata in ``corpus.document_legal_meta`` (corpus migration 0010).

Features:
    US-KOR-02, US-ZRD-05, F-12
"""

from collections.abc import Sequence
from typing import Final, LiteralString

from psycopg import AsyncConnection, Error
from psycopg.rows import class_row

from meritum_core.corpus.errors import CorpusUnavailableError
from meritum_core.corpus.models import LegalActMeta

_UPSERT: Final[LiteralString] = """
INSERT INTO corpus.document_legal_meta (source_id, eli, document_type,
    legal_status, in_force, in_force_from, in_force_until, journal_publisher,
    journal_year, journal_position, display_address)
VALUES (%(source_id)s, %(eli)s, %(document_type)s, %(legal_status)s,
    %(in_force)s, %(in_force_from)s, %(in_force_until)s, %(journal_publisher)s,
    %(journal_year)s, %(journal_position)s, %(display_address)s)
ON CONFLICT (source_id) DO UPDATE SET eli = EXCLUDED.eli,
    document_type = EXCLUDED.document_type, legal_status = EXCLUDED.legal_status,
    in_force = EXCLUDED.in_force, in_force_from = EXCLUDED.in_force_from,
    in_force_until = EXCLUDED.in_force_until,
    journal_publisher = EXCLUDED.journal_publisher,
    journal_year = EXCLUDED.journal_year,
    journal_position = EXCLUDED.journal_position,
    display_address = EXCLUDED.display_address, updated_at = now()
"""
"""Insert or replace one document's row; a refetch of the act overwrites it."""

_READ: Final[LiteralString] = """
SELECT source_id, eli, document_type, legal_status, in_force, in_force_from,
    in_force_until, journal_publisher, journal_year, journal_position,
    display_address
FROM corpus.document_legal_meta
WHERE source_id = ANY(%s)
"""
"""The rows of the given documents; a page outside ELI has none."""


class _Row(LegalActMeta):
    source_id: str


class PostgresLegalActMeta:
    """LegalActMetaPort over the shared ``corpus`` schema.

    Args:
        conninfo: libpq connection string.

    Features:
        US-KOR-02, US-ZRD-05, F-12
    """

    def __init__(self, conninfo: str) -> None:
        self._conninfo = conninfo

    async def save(self, source_id: str, meta: LegalActMeta) -> None:
        """Upsert the act's metadata (see ``LegalActMetaPort.save``).

        Args:
            source_id: The document; its ``corpus.documents`` row must exist.
            meta: The act's metadata.

        Raises:
            CorpusUnavailableError: PostgreSQL failed or the document is missing.
        """
        params = {"source_id": source_id, **meta.model_dump()}
        try:
            async with await AsyncConnection.connect(self._conninfo) as conn:
                await conn.execute(_UPSERT, params)
        except Error as exc:
            msg = "saving legal act metadata failed in PostgreSQL"
            raise CorpusUnavailableError(msg) from exc

    async def read(self, source_ids: Sequence[str]) -> dict[str, LegalActMeta]:
        """Read the metadata (see ``LegalActMetaPort.read``).

        Args:
            source_ids: Documents to look up.

        Returns:
            Metadata per ``source_id`` of the legal acts among them.

        Raises:
            CorpusUnavailableError: PostgreSQL failed.
        """
        try:
            async with (
                await AsyncConnection.connect(self._conninfo) as conn,
                conn.cursor(row_factory=class_row(_Row)) as cursor,
            ):
                await cursor.execute(_READ, (list(source_ids),))
                rows = await cursor.fetchall()
        except Error as exc:
            msg = "reading legal act metadata failed in PostgreSQL"
            raise CorpusUnavailableError(msg) from exc
        return {
            r.source_id: LegalActMeta.model_validate(
                r.model_dump(exclude={"source_id"})
            )
            for r in rows
        }
