"""Settings and weights of the agent-ready corpus layer (``corpus_ready``).

Features:
    US-KOR-02, US-ZRD-05, F-12
"""

from typing import Final

READY_FLAG_ENV: Final = "MERITUM_CORPUS_READY"
"""Switch of the whole layer; unset or false keeps every path as it was."""

GOLD_ID_PREFIX: Final = "gold:"
"""Prefix of a gold chunk's ``passage_id``, so it never collides with bronze ids."""

ACT_IN_WINDOW_WEIGHT: Final = 1.0
"""Weight of an act in force on the claim date (ingest-lab C2, research-ingest §0.1)."""

ACT_OUT_OF_WINDOW_WEIGHT: Final = 0.6
"""Weight of an act not in force on the claim date; kept, not filtered, because an
expired act can be the only source for a claim about its own year."""

STUB_WEIGHT: Final = 0.3
"""Base weight the builder gives a title-only document (no body to cite)."""

READY_MIGRATIONS_LOCK: Final = 4_201_168
"""Advisory lock key of the corpus_ready migration runner (one runner at a time)."""

READY_MIGRATION_SUFFIX: Final = ".sql"
"""File suffix of a corpus_ready migration in ``ready/migrations``."""
