"""Meritum's own catalogue filter: the second control after the provider's sites.

Features:
    US-KOR-04, F-13, ADR-07
"""

from collections.abc import Sequence
from urllib.parse import unquote, urlsplit

from meritum_core.checks.contracts import CatalogEntry
from meritum_core.corpus.web_search.constants import (
    DOT_SEGMENTS,
    PATH_SEPARATORS,
    WEB_SCHEMES,
    WWW_PREFIX,
)


def _host(host: str) -> str:
    return host.lower().removeprefix(WWW_PREFIX)


def _segments(path: str) -> list[str]:
    return [part for part in path.split("/") if part]


def _split(entry: CatalogEntry) -> tuple[str, list[str]]:
    entry_host, _, entry_path = entry.domain.partition("/")
    return _host(entry_host), _segments(entry_path)


def _is_tricky(segment: str) -> bool:
    decoded = unquote(segment)
    return decoded in DOT_SEGMENTS or any(s in decoded for s in PATH_SEPARATORS)


def _matches(host: str, path: list[str], entry: CatalogEntry) -> bool:
    wanted, prefix = _split(entry)
    same_site = host == wanted or host.endswith(f".{wanted}")
    return same_site and path[: len(prefix)] == prefix


def _specificity(entry: CatalogEntry) -> tuple[int, int]:
    wanted, prefix = _split(entry)
    return len(prefix), len(wanted)


def catalog_entry_for(url: str, catalog: Sequence[CatalogEntry]) -> CatalogEntry | None:
    """Find the catalogue entry an address belongs to, the most specific one first.

    An entry matches its host, its subdomains and, when it names a path
    (``www.gov.pl/web/gis``), only addresses under that path, segment by segment.
    ``www.`` is ignored on both sides. Excluded entries and source-status lists
    never match: their pages are not evidence.

    Args:
        url: a result address from a provider.
        catalog: the loaded catalogue.

    Returns:
        The matching entry, or None for an address outside the catalogue or
        one that is not a plain http(s) URL with a host, or whose path holds
        ``.`` or ``..`` segments or encoded separators (``%2f``, ``%5c``) or ``;``.

    Features:
        US-KOR-04, F-13, ADR-07
    """
    parts = urlsplit(url)
    has_credentials = "@" in parts.netloc
    if parts.scheme not in WEB_SCHEMES or parts.hostname is None or has_credentials:
        return None
    host, path = _host(parts.hostname), _segments(parts.path)
    if any(map(_is_tricky, path)):
        return None
    usable = (e for e in catalog if not e.excluded and e.role == "evidence")
    found = [e for e in usable if _matches(host, path, e)]
    return max(found, key=_specificity, default=None)
