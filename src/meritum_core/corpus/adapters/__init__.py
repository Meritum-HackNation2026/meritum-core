"""Corpus search adapters, built only by ``meritum_core.corpus.factory``.

Features:
    US-KOR-02, F-12, ADR-04
"""

from ._memory import MemoryCorpusSearch
from ._postgres import PostgresCorpusSearch

__all__ = ["MemoryCorpusSearch", "PostgresCorpusSearch"]
