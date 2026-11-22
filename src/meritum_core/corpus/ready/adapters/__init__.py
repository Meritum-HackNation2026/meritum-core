"""Adapters of the corpus_ready layer, for the corpus factory and worker wiring only.

Features:
    US-KOR-02, F-12
"""

from ._migrations import apply_corpus_ready_migrations
from ._postgres import PostgresGoldSearch

__all__ = ["PostgresGoldSearch", "apply_corpus_ready_migrations"]
