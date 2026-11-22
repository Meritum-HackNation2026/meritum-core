"""The kind of one document: a catalogue entry's path rules over its domain kind.

Features:
    US-ZRD-12, US-KOR-01
"""

from urllib.parse import urlsplit

from ._sources import CatalogEntry
from ._types import SourceKind


def kind_for(entry: CatalogEntry, url: str) -> SourceKind:
    """The kind of one document: the first matching path rule, else ``entry.kind``.

    Args:
        entry: the catalogue entry of the document's domain.
        url: the document's URL.

    Returns:
        The source kind to show for that document.

    Features:
        US-ZRD-12, US-KOR-01
    """
    path = urlsplit(url).path
    return next(
        (kind for part, kind in entry.kind_by_path.items() if part in path),
        entry.kind,
    )
