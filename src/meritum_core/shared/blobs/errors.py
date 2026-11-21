"""Errors of the blob store port.

Features:
    US-SPR-11, US-BEZ-05, ADR-31
"""


class BlobError(Exception):
    """Base error of every BlobStore adapter.

    Features:
        ADR-31
    """


class BlobNotFoundError(BlobError, LookupError):
    """No such blob: never stored, deleted with its session, expired or malformed id.

    Features:
        US-BEZ-05, ADR-31
    """
