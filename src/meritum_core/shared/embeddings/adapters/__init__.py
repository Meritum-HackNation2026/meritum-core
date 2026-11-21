"""Embeddings adapters, built only by ``meritum_core.shared.embeddings.factory``.

Features:
    US-KOR-02, F-12, ADR-04
"""

from ._stub import StubEmbeddings
from ._vertex import VertexEmbeddings

__all__ = ["StubEmbeddings", "VertexEmbeddings"]
