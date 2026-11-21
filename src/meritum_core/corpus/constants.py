"""Weights and thresholds of the corpus search, tuned only on the golden set.

Features:
    US-KOR-02, US-ZRD-05, F-12, ADR-04
"""

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
"""Lowest freshness weight, also used for passages without a publication date:
an old but much better match still beats a fresh weak one."""

TRIGRAM_THRESHOLD: Final = 0.3
"""Lowest pg_trgm word similarity for the typo ranking (pg_trgm default 0.6
misses most one-letter typos in short Polish words)."""

MEMORY_STEM_LENGTH: Final = 5
"""The in-memory adapter compares word prefixes of this length, a stand-in for
the hunspell dictionary of ``public.polish`` in PostgreSQL."""
