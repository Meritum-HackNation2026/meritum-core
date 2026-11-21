"""Errors of the corpus search.

Features:
    US-KOR-02, F-12, ADR-19
"""


class UnknownCorpusVersionError(Exception):
    """The pinned ``corpus_version`` names no snapshot.

    Searching another snapshot instead would break channel consistency (ADR-19).

    Features:
        US-KOR-02, F-12, ADR-19
    """


class CorpusUnavailableError(Exception):
    """The corpus database failed; callers map it to ``technical_failure``.

    Features:
        US-KOR-02, F-12, ADR-04
    """


class InvalidCatalogError(ValueError):
    """The source catalogue file is malformed or one of its entries breaks a rule.

    The message names the entry (``entries[<index>] <domain>``) so a curator can fix it.

    Features:
        US-KOR-01, F-10
    """
