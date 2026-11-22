"""Contract v18: the source kind ``transcript`` and per-path kinds in the catalogue (core#135).

Features:
    US-ZRD-12, US-KOR-01, ADR-02
"""

from meritum_core.checks import contracts as c
from meritum_core.corpus.catalog import load_catalog

SEJM = "https://api.sejm.gov.pl/sejm/term10/proceedings/5/2026-01-09/transcripts/12/3"
ELI = "https://api.sejm.gov.pl/eli/acts/DU/2024/1"


def _entry(**extra: object) -> c.CatalogEntry:
    return c.CatalogEntry.model_validate(
        {
            "domain": "api.sejm.gov.pl",
            "publisher": "Kancelaria Sejmu",
            "publisher_id": "kancelaria-sejmu",
            "kind": "akt_prawny",
            "tier": "primary",
            "license": "materiał urzędowy",
            "ingest": "api",
            "qualified_because": "Oficjalne API Sejmu z aktami i stenogramami.",
            **extra,
        }
    )


def test_version_is_18() -> None:
    assert c.CONTRACT_VERSION == 18


def test_transcript_is_a_source_kind() -> None:
    assert _entry(kind="transcript").kind == "transcript"


def test_entry_without_path_rules_keeps_its_kind() -> None:
    assert c.kind_for(_entry(), SEJM) == "akt_prawny"


def test_path_rule_overrides_the_domain_kind() -> None:
    entry = _entry(kind_by_path={"/transcripts/": "transcript"})
    assert c.kind_for(entry, SEJM) == "transcript"
    assert c.kind_for(entry, ELI) == "akt_prawny"


def test_sejm_catalogue_entry_marks_transcripts() -> None:
    entry = next(e for e in load_catalog() if e.domain == "api.sejm.gov.pl")
    assert c.kind_for(entry, SEJM) == "transcript"
    assert c.kind_for(entry, ELI) == "akt_prawny"
