"""Corpus search and legal act metadata adapters, built only by ``corpus.factory``.

Features:
    US-KOR-02, F-12, ADR-04
"""

from ._legal_meta import PostgresLegalActMeta
from ._memory import MemoryCorpusSearch
from ._postgres import PostgresCorpusSearch

__all__ = ["MemoryCorpusSearch", "PostgresCorpusSearch", "PostgresLegalActMeta"]
