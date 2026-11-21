"""Errors of the embeddings port.

Features:
    US-KOR-02, F-12, ADR-04
"""


class EmbeddingsUnavailableError(Exception):
    """The provider failed after all retries; callers map it to ``technical_failure``.

    Features:
        US-KOR-02, F-12, ADR-04
    """
