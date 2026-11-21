"""The catalogue exports to catalog/catalog.json and to the audit table in the README."""

import json
from pathlib import Path

from meritum_core.checks.contracts import CatalogEntry
from meritum_core.corpus.catalog import (
    catalog_json,
    catalog_markdown,
    catalog_yaml,
    load_catalog,
)
from meritum_core.corpus.constants import CATALOG_FILE

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


def test_yaml_export_reproduces_the_shipped_catalogue_byte_for_byte() -> None:
    shipped = CATALOG_FILE.read_text(encoding="utf-8")
    assert catalog_yaml(load_catalog(), shipped) == shipped


def test_yaml_export_writes_an_exclusion_and_reloads(tmp_path: Path) -> None:
    path = tmp_path / "catalog.yaml"
    path.write_text(catalog_yaml((EXCLUDED,), "# nagłówek\n"), encoding="utf-8")
    assert load_catalog(path) == (EXCLUDED,)
    assert path.read_text(encoding="utf-8").startswith("# nagłówek\n")


def test_yaml_export_keeps_a_filled_list_and_an_included_entry(tmp_path: Path) -> None:
    signatory = EXCLUDED.model_copy(
        update={"excluded": False, "exclusion_reason": None, "signatory_of": ["ifcn"]}
    )
    path = tmp_path / "catalog.yaml"
    path.write_text(catalog_yaml((signatory,), ""), encoding="utf-8")
    assert load_catalog(path) == (signatory,)
    assert "excluded" not in path.read_text(encoding="utf-8")
