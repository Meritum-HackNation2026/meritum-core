"""The source catalogue loads from YAML and every entry validates as CatalogEntry."""

from pathlib import Path

import pytest

from meritum_core.corpus.catalog import InvalidCatalogError, load_catalog

ENTRY = """
  - domain: fakenews.pl
    publisher: Stowarzyszenie Demagog
    publisher_id: fakenews
    kind: fact_check
    tier: secondary
    license: prawo cytatu
    ingest: rss
    qualified_because: Sygnatariusz IFCN bez blokad dla robotów.
"""


def test_catalogue_has_primary_sources_of_citizens_money_questions() -> None:
    entries = {e.domain: e for e in load_catalog()}
    citizens = ["www.gov.pl/web/rodzina", "www.gov.pl/web/finanse", "podatki.gov.pl"]
    citizens += ["www.zus.pl", "stat.gov.pl", "www.prezydent.pl"]
    for domain in citizens:
        assert entries[domain].tier == "primary", domain
        assert not entries[domain].excluded, domain
    assert entries["www.sejm.gov.pl"].excluded
    assert entries["www.sejm.gov.pl"].exclusion_reason is not None


def _write(tmp_path: Path, body: str) -> Path:
    path = tmp_path / "catalog.yaml"
    path.write_text(body, encoding="utf-8")
    return path


def test_shipped_catalogue_has_the_curated_entries() -> None:
    entries = {e.domain: e for e in load_catalog()}
    assert len(entries) == 64
    assert entries["euvsdisinfo.eu"].publisher_id == "eeas-euvsdisinfo"
    assert entries["euvsdisinfo.eu"].ingest == "mcp"
    assert entries["konkret24.tvn24.pl"].excluded
    assert (
        entries["demagog.org.pl"].ingest
        == entries["sprawdzam.afp.com"].ingest
        == "live"
    )
    assert entries["hole.cert.pl"].role == "source_status"


def test_entry_without_reason_for_exclusion_names_the_entry(tmp_path: Path) -> None:
    broken = ENTRY.replace("fakenews.pl", "konkret24.tvn24.pl") + "    excluded: true\n"
    path = _write(tmp_path, "entries:" + ENTRY + broken)
    with pytest.raises(InvalidCatalogError, match=r"entries\[1\] konkret24\.tvn24\.pl"):
        load_catalog(path)


def test_file_without_entries_list_is_rejected(tmp_path: Path) -> None:
    with pytest.raises(InvalidCatalogError, match="entries"):
        load_catalog(_write(tmp_path, "- domain: x\n"))


def test_domain_listed_twice_is_rejected(tmp_path: Path) -> None:
    path = _write(tmp_path, "entries:" + ENTRY + ENTRY)
    with pytest.raises(InvalidCatalogError, match=r"fakenews\.pl.*twice"):
        load_catalog(path)
