"""Exports of the catalogue: JSON for the web app and a Markdown audit table.

Features:
    US-KOR-01, F-10
"""

import json
from collections.abc import Sequence

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
