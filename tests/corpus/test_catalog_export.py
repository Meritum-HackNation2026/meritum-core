"""The catalogue exports to catalog/catalog.json and to the audit table in the README."""

import json

from meritum_core.checks.contracts import CatalogEntry
from meritum_core.corpus.catalog import catalog_json, catalog_markdown, load_catalog

EXCLUDED = CatalogEntry(
    domain="konkret24.tvn24.pl",
    publisher="TVN | Konkret24",
    publisher_id="konkret24",
    kind="fact_check",
    tier="secondary",
    license="umowa licencyjna",
    ingest="static",
    qualified_because="Redakcja fact-checkingowa TVN24.",
    excluded=True,
    exclusion_reason="Brak w IFCN i EFCSN.",
)


def test_json_lists_every_entry_with_all_fields() -> None:
    entries = load_catalog()
    exported = json.loads(catalog_json(entries))
    assert [e["domain"] for e in exported["entries"]] == [e.domain for e in entries]
    assert set(exported["entries"][0]) == set(CatalogEntry.model_fields)


def test_json_ends_with_a_newline() -> None:
    assert catalog_json(load_catalog()).endswith("}\n")


def test_markdown_row_shows_exclusion_reason_and_escapes_pipes() -> None:
    table = catalog_markdown((EXCLUDED,))
    row = table.splitlines()[-1]
    assert "TVN \\| Konkret24" in row
    assert "wykluczone: Brak w IFCN i EFCSN." in row
