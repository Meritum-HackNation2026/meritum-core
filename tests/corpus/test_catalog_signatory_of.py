"""Fact-checkers in the shipped catalogue declare IFCN/EFCSN membership (ADR-34)."""

from meritum_core.corpus.catalog import load_catalog

SIGNATORY_EXPECTATIONS = {
    "fakenews.pl": ["ifcn"],
    "pravda.org.pl": ["ifcn", "efcsn"],
    "demagog.org.pl": ["ifcn", "efcsn"],
    "sprawdzam.afp.com": ["ifcn", "efcsn"],
    "konkret24.tvn24.pl": [],
}

NON_CLAIMREVIEW_FACT_CHECKERS = (
    "euvsdisinfo.eu",
    "edmo.eu",
    "checkfirst.network",
    "www.nask.pl",
)


def test_fact_checkers_declare_signatory_membership() -> None:
    """The listed publishers match IFCN/EFCSN lists checked on 2026-11-21."""
    by_domain = {entry.domain: entry for entry in load_catalog()}
    for domain, expected in SIGNATORY_EXPECTATIONS.items():
        assert by_domain[domain].signatory_of == expected, domain

    for domain in NON_CLAIMREVIEW_FACT_CHECKERS:
        assert by_domain[domain].signatory_of == [], domain
