"""Text embeddings behind ``EmbeddingsPort``; the provider is picked by configuration.

Public API: the port, its settings, the factory and its error.

Features:
    US-KOR-02, F-12, ADR-04
"""

from meritum_core.shared.embeddings.errors import EmbeddingsUnavailableError
from meritum_core.shared.embeddings.factory import build_embeddings
from meritum_core.shared.embeddings.ports import EmbeddingsPort, Vector
from meritum_core.shared.embeddings.settings import (
    EmbeddingsProvider,
    EmbeddingsSettings,
)

__all__ = [
    "EmbeddingsPort",
    "EmbeddingsProvider",
    "EmbeddingsSettings",
    "EmbeddingsUnavailableError",
    "Vector",
    "build_embeddings",
]
