"""Verbatim citation check: find_verbatim and verify_citation (US-ZRD-01, F-16, ADR-06)."""

from typing import Any

import pytest

from meritum_core.checks.contracts import Source
from meritum_core.evidence import (
    CitationDraft,
    SourceDocument,
    find_verbatim,
    verify_citation,
)

SOURCE: dict[str, Any] = {
    "id": "imgw-ostrzezenie-1",
    "title": "Ostrzeżenia meteorologiczne",
    "publisher": "IMGW-PIB",
    "publisher_id": "imgw",
    "url": "https://meteo.imgw.pl/ostrzezenia",
    "domain": "meteo.imgw.pl",
    "kind": "instytucja",
    "tier": "primary",
    "fetched_at": "2026-11-21T12:00:00+01:00",
}
TEXT = (
    "Komunikat IMGW.\n\nOstrzeżenie  II stopnia \u2013 burze z gradem \u2013 obowiązuje do 18:00.\n"
    "Prognozowane są „opady deszczu” do 30 mm.\n\n"
    "Zalecamy ostrożność.\nŹródło: IMGW-PIB, wydział łączności."
)
DOCUMENTS = {
    SOURCE["id"]: SourceDocument(source=Source.model_validate(SOURCE), text=TEXT)
}


def _draft(fragment: str, **extra: str) -> CitationDraft:
    return CitationDraft.model_validate(
        {"source_id": SOURCE["id"], "fragment": fragment, "stance": "supports"} | extra
    )


def test_exact_fragment_returns_its_position_in_the_source() -> None:
    span = find_verbatim("Zalecamy ostrożność.", TEXT)
    assert span is not None
    assert TEXT[span[0] : span[1]] == "Zalecamy ostrożność."


def test_whitespace_quotes_and_dashes_differences_still_match() -> None:
    fragment = 'Ostrzeżenie II stopnia - burze z gradem — obowiązuje do 18:00. Prognozowane są "opady deszczu"'
    span = find_verbatim(fragment, TEXT)
    assert span is not None
    assert TEXT[span[0] : span[1]].startswith("Ostrzeżenie  II stopnia \u2013")
    assert TEXT[span[0] : span[1]].endswith("„opady deszczu”")


def test_fragment_spanning_paragraphs_matches() -> None:
    assert (
        find_verbatim("do 30 mm. Zalecamy ostrożność. Źródło: IMGW-PIB", TEXT)
        is not None
    )


def test_long_quote_matches() -> None:
    long_text = " ".join(f"Zdanie numer {i} o łączności żółwia." for i in range(200))
    fragment = long_text[1000:4000].strip()
    span = find_verbatim(fragment, long_text)
    assert span is not None
    assert long_text[span[0] : span[1]] == fragment


@pytest.mark.parametrize(
    "fragment",
    [
        "Ostrzezenie II stopnia",  # Polish letters are not folded
        "ostrzeżenie II stopnia",  # case is not folded
        "Ostrzeżenie II stopnia obowiązuje do 18:00",  # paraphrase: words skipped
        "Szkoły są zamknięte do odwołania",
        "   ",
    ],
)
def test_anything_beyond_the_normalization_does_not_match(fragment: str) -> None:
    assert find_verbatim(fragment, TEXT) is None


def test_verified_citation_takes_metadata_from_the_database_not_the_model() -> None:
    draft = _draft(
        "Zalecamy  ostrożność. Źródło: IMGW-PIB",
        title="Zmyślony tytuł",
        publisher="Zmyślony wydawca",
        url="https://zmyslone.example.com",
    )
    citation = verify_citation(draft, DOCUMENTS)
    assert citation is not None
    assert citation.source == DOCUMENTS[SOURCE["id"]].source
    assert citation.fragment == "Zalecamy ostrożność.\nŹródło: IMGW-PIB"
    assert citation.stance == "supports"
    assert citation.fragment_found_verbatim is True


def test_invented_fragment_is_dropped() -> None:
    assert (
        verify_citation(_draft("Szkoły są zamknięte do odwołania"), DOCUMENTS) is None
    )


def test_unknown_source_id_is_dropped() -> None:
    draft = _draft("Zalecamy ostrożność.", source_id="brak-w-bazie")
    assert verify_citation(draft, DOCUMENTS) is None


def test_fragment_outside_the_citation_length_limits_is_dropped() -> None:
    assert verify_citation(_draft("IMGW."), DOCUMENTS) is None
