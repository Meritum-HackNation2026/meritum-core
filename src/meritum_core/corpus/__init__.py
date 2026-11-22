"""Corpus slice: the audited source catalogue and its hybrid search.

Public API: the search port, its result model, the fusion rule, settings and
the factory. Research agents (worker) and the MCP tool ``search_sources``
(backend) call ``CorpusSearchPort`` in process (ADR-32). The worker passes
the passages through ``RerankerPort`` before stance assessment (ADR-35).
``LegalActMetaPort`` keeps what ELI says about a legal act per document; it is
internal to the corpus, not part of the checks contract.

Features:
    US-KOR-02, US-ZRD-05, US-SPR-04, F-12, ADR-04, ADR-19, ADR-32, ADR-35
"""

from meritum_core.corpus.errors import (
    CorpusUnavailableError,
    UnknownCorpusVersionError,
)
from meritum_core.corpus.factory import build_corpus_search, build_legal_act_meta
from meritum_core.corpus.fusion import freshness_weight, fuse_rankings
from meritum_core.corpus.models import LegalActMeta, Passage
from meritum_core.corpus.ports import CorpusSearchPort, LegalActMetaPort
from meritum_core.corpus.rerank import (
    RERANK_TOP_K,
    NullReranker,
    RankedPassage,
    RerankerPort,
)
from meritum_core.corpus.settings import CorpusProvider, CorpusSettings

__all__ = [
    "RERANK_TOP_K",
    "CorpusProvider",
    "CorpusSearchPort",
    "CorpusSettings",
    "CorpusUnavailableError",
    "LegalActMeta",
    "LegalActMetaPort",
    "NullReranker",
    "Passage",
    "RankedPassage",
    "RerankerPort",
    "UnknownCorpusVersionError",
    "build_corpus_search",
    "build_legal_act_meta",
    "freshness_weight",
    "fuse_rankings",
]
