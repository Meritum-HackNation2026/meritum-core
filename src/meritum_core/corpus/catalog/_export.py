"""Exports of the catalogue: JSON for the web app and a Markdown audit table.

Features:
    US-KOR-01, F-10
"""

import json
from collections.abc import Sequence
from itertools import takewhile

import yaml

from meritum_core.checks.contracts import CatalogEntry
from meritum_core.corpus.constants import CATALOG_TABLE_HEADER


def catalog_json(entries: Sequence[CatalogEntry]) -> str:
    """Serialise the catalogue as ``catalog/catalog.json`` for "Jak działa Meritum".

    Args:
        entries: the validated catalogue.

    Returns:
        ``{"entries": [...]}`` with every CatalogEntry field, two-space indented.

    Features:
        US-KOR-01, F-10
    """
    payload = {"entries": [e.model_dump(mode="json") for e in entries]}
    return json.dumps(payload, ensure_ascii=False, indent=2) + "\n"


def _cell(value: object) -> str:
    return "" if value is None else str(value).replace("|", "\\|")


def _row(e: CatalogEntry) -> str:
    state = f"wykluczone: {e.exclusion_reason}" if e.excluded else "włączone"
    cells = (
        f"`{e.domain}`",
        f"{e.publisher} (`{e.publisher_id}`)",
        e.tier,
        e.role,
        e.ingest,
        e.refresh_minutes,
        e.validity if e.max_age_hours is None else f"{e.validity}, {e.max_age_hours} h",
        e.tdm_reservation,
        state,
    )
    return "| " + " | ".join(map(_cell, cells)) + " |"


def catalog_markdown(entries: Sequence[CatalogEntry]) -> str:
    """Render the catalogue as the Markdown audit table of the README.

    Args:
        entries: the validated catalogue.

    Returns:
        A table with one row per entry, in catalogue order.

    Features:
        US-KOR-01, F-10
    """
    return "\n".join([CATALOG_TABLE_HEADER, *map(_row, entries)])


def _yaml_entry(entry: CatalogEntry) -> str:
    dumped_fields = entry.model_dump(mode="json", exclude_none=True)
    fields = {k: v for k, v in dumped_fields.items() if v != []}  # e.g. signatory_of
    if not entry.excluded:
        del fields["excluded"]
    dumped = yaml.safe_dump([fields], allow_unicode=True, sort_keys=False, width=10_000)
    return str(dumped)  # PyYAML ships no stubs


def catalog_yaml(entries: Sequence[CatalogEntry], current: str) -> str:
    """Render the catalogue back to ``catalog.yaml`` in the curators' layout.

    Keeps the leading comment lines of ``current``, omits empty fields, empty
    lists and ``excluded: false`` and puts a blank line between entries, so rewriting an
    unchanged catalogue gives the same bytes.

    Args:
        entries: the validated catalogue.
        current: the file's present text, for its leading comments.

    Returns:
        The YAML text.

    Features:
        US-KOR-01, F-10
    """
    lines = current.splitlines(keepends=True)
    header = "".join(takewhile(lambda line: line.startswith("#"), lines))
    return header + "\nentries:\n\n" + "\n".join(map(_yaml_entry, entries))
