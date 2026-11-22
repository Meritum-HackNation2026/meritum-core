"""EUvsDisinfo carries the site's own disclaimer in the catalogue (core#146)."""

from meritum_core.corpus.catalog import load_catalog


def test_euvsdisinfo_entry_has_disclaimer_and_others_do_not() -> None:
    """The text lives in catalog.yaml, so no consumer hard-codes it."""
    by_id = {entry.publisher_id: entry for entry in load_catalog()}
    assert "nie stanowią oficjalnego stanowiska Unii Europejskiej" in (
        by_id["eeas-euvsdisinfo"].disclaimer or ""
    )
    assert by_id["demagog"].disclaimer is None
