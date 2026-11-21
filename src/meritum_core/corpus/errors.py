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
