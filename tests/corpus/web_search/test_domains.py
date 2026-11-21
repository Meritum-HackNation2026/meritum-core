"""The catalogue filter: hosts, subdomains, paths and entries that never match."""

import pytest

from meritum_core.corpus.web_search import catalog_entry_for

from .conftest import entry

CATALOG = (
    entry("gov.pl", "gov"),
    entry("www.gov.pl/web/gis/ostrzezenia", "gis"),
    entry("policja.pl", "kgp"),
    entry("sankcje.example", "mswia", role="source_status"),
    entry(
        "wykluczony.example",
        "wykluczony",
        excluded=True,
        exclusion_reason="Zastrzeżenie TDM w robots.txt.",
    ),
)


@pytest.mark.parametrize(
    ("url", "publisher_id"),
    [
        ("https://gov.pl/", "gov"),
        ("https://www.gov.pl/web/rcb", "gov"),
        ("https://www.gov.pl/web/gis/ostrzezenia", "gis"),
        ("https://gov.pl/web/gis/ostrzezenia/komunikat-1?x=1", "gis"),
        ("https://www.gov.pl/web/gis/ostrzezenia-stare", "gov"),
        ("http://WWW.POLICJA.PL/pol/aktualnosci", "kgp"),
        ("https://krakow.policja.pl/", "kgp"),
    ],
)
def test_address_gets_its_most_specific_entry(url: str, publisher_id: str) -> None:
    found = catalog_entry_for(url, CATALOG)
    assert found is not None
    assert found.publisher_id == publisher_id


@pytest.mark.parametrize(
    "url",
    [
        "https://example.com/burze",
        "https://notgov.pl/",
        "https://gov.pl.evil.example/",
        "https://sankcje.example/lista",
        "https://wykluczony.example/",
        "ftp://gov.pl/plik",
        "https://user:pass@gov.pl/",
        "gov.pl/web",
        "https://www.gov.pl/web/gis/ostrzezenia/../../../web/obca",
        "https://www.gov.pl/web/gis/ostrzezenia/%2e%2e/x",
        "https://www.gov.pl/web/gis/./ostrzezenia",
        "https://www.gov.pl/web/gis/ostrzezenia/%2e%2e%2f%2e%2e%2fobca",
        "https://www.gov.pl/web/gis/ostrzezenia/..%5c..%5cobca",
        "https://www.gov.pl/web/gis/ostrzezenia/..;/..;/obca",
        "",
    ],
)
def test_address_outside_the_catalogue_matches_nothing(url: str) -> None:
    assert catalog_entry_for(url, CATALOG) is None
