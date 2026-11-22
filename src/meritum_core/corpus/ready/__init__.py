"""Agent-ready corpus layer (``corpus_ready``): silver text and gold chunks.

Bronze is ``corpus.documents`` as it is. Silver is its text cleaned without an
LLM; gold is retrieval-ready chunks with a header, tags, a weight and an
embedding, each pointing back to bronze ``source_id`` and character offsets.
Everything is off unless ``MERITUM_CORPUS_READY`` is true. The worker builds the
layer; ``build_corpus_search`` reads it for research agents and ``search_sources``.

Features:
    US-KOR-02, US-ZRD-05, F-12
"""

from meritum_core.corpus.ready.constants import GOLD_ID_PREFIX, STUB_WEIGHT
from meritum_core.corpus.ready.merge import fuse_gold, merge_with_bronze
from meritum_core.corpus.ready.models import DocumentKind, GoldChunk, GoldHit, NumberTag
from meritum_core.corpus.ready.settings import CorpusReadySettings
from meritum_core.corpus.ready.weighting import gold_weight

__all__ = [
    "GOLD_ID_PREFIX",
    "STUB_WEIGHT",
    "CorpusReadySettings",
    "DocumentKind",
    "GoldChunk",
    "GoldHit",
    "NumberTag",
    "fuse_gold",
    "gold_weight",
    "merge_with_bronze",
]
