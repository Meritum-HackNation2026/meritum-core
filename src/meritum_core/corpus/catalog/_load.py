"""Loading the source catalogue YAML and validating each entry as CatalogEntry.

Features:
    US-KOR-01, US-KOR-05, F-10
"""

from itertools import starmap
from pathlib import Path

import yaml
from pydantic import ValidationError

from meritum_core.checks.contracts import CatalogEntry
from meritum_core.corpus.constants import CATALOG_FILE
from meritum_core.corpus.errors import InvalidCatalogError


def _entry(index: int, raw: object) -> CatalogEntry:
    label = raw.get("domain", "?") if isinstance(raw, dict) else "?"
    try:
        return CatalogEntry.model_validate(raw)
    except ValidationError as error:
        msg = f"entries[{index}] {label}: {error}"
        raise InvalidCatalogError(msg) from error


def load_catalog(path: Path = CATALOG_FILE) -> tuple[CatalogEntry, ...]:
    """Read the catalogue and validate every entry, in file order.

    Args:
        path: a YAML file with one ``entries:`` list of CatalogEntry mappings.

    Returns:
        The validated entries.

    Raises:
        InvalidCatalogError: The file has no ``entries`` list, an entry breaks a
            CatalogEntry rule, or a domain is listed twice.

    Features:
        US-KOR-01, US-KOR-05, F-10
    """
    document = yaml.safe_load(path.read_text(encoding="utf-8"))
    raw = document.get("entries") if isinstance(document, dict) else None
    if not isinstance(raw, list):
        msg = f"{path} needs a top-level 'entries' list"
        raise InvalidCatalogError(msg)
    entries = tuple(starmap(_entry, enumerate(raw)))
    seen: set[str] = set()
    for index, entry in enumerate(entries):
        if entry.domain in seen:
            msg = f"entries[{index}] {entry.domain}: domain listed twice"
            raise InvalidCatalogError(msg)
        seen.add(entry.domain)
    return entries
