"""Weights and thresholds of the corpus search, tuned only on the golden set.

Features:
    US-KOR-02, US-ZRD-05, F-12, ADR-04
"""

from pathlib import Path
from typing import Final

ENV_PREFIX: Final = "MERITUM_CORPUS_"
"""Prefix of every corpus setting in the environment (ADR-32)."""

DEFAULT_LIMIT: Final = 10
"""Passages one search returns unless the caller asks for another number."""

CANDIDATES_PER_RANKING: Final = 50
"""Passages each ranking (vector, full text, trigram) hands to the fusion."""

RRF_K: Final = 60
"""Reciprocal rank fusion constant: a passage at rank r adds 1 / (RRF_K + r).
60 is the value from the original RRF paper; larger flattens the rank curve."""

FRESHNESS_HALF_LIFE_DAYS: Final = 180
"""Age, relative to the claim date, at which the freshness bonus halves
(US-ZRD-05): a 180-day-old passage keeps 75% of its fused score."""

FRESHNESS_FLOOR: Final = 0.5
"""Lowest freshness weight, also used for passages without a publication date.
With RRF_K = 60 a passage 400 days old that tops all three rankings (score
~0.030) loses to a fresh one ranked about 30th in all three (~0.033) and beats
one found by a single ranking. Tune both on the golden set (ADR-28)."""

TRIGRAM_THRESHOLD: Final = 0.3
"""Lowest pg_trgm word similarity for the typo ranking (pg_trgm default 0.6
misses most one-letter typos in short Polish words)."""

MEMORY_STEM_LENGTH: Final = 5
"""The in-memory adapter compares word prefixes of this length, a stand-in for
the hunspell dictionary of ``public.polish`` in PostgreSQL."""

CATALOG_FILE: Final = Path(__file__).parent / "catalog" / "catalog.yaml"
"""The audited source catalogue shipped with the package (US-KOR-01, F-10);
``scripts/export_catalog.py`` turns it into ``catalog/catalog.json``."""

TDM_EXCLUSION_REASON: Final = (
    "Content-Signal w robots.txt albo znaczniki meta zastrzegają eksplorację "
    "tekstów i danych (art. 4 dyrektywy 2019/790)."
)
"""Exclusion reason the TDM check writes into a secondary source whose owner
reserved text and data mining (US-KOR-01, ADR-24); catalogue data, not UI copy."""

FULL_TEXT_RETENTION_DAYS: Final = 90
"""Days a fetched document's full text is kept, counted from ``fetched_at``
(US-KOR-05). Metadata and cited fragments stay as long as the check record."""

CATALOG_TABLE_HEADER: Final = (
    "| Domena | Wydawca (`publisher_id`) | Poziom | Rola | Pobieranie "
    "| Odświeżanie (min) | Ważność | Zastrzeżenie TDM | Stan |\n"
    "|---|---|---|---|---|---|---|---|---|"
)
"""Header of the generated audit table of the catalogue in the README (US-KOR-01)."""

TDM_SIGNAL_USES: Final = frozenset({"ai-train", "ai-input"})
"""Content-Signal uses whose ``=no`` reserves text and data mining (ADR-24);
a plain ``Disallow`` blocks crawling and is recorded as an exclusion instead."""
