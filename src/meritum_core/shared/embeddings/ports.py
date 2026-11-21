"""The embeddings port: queries and documents embedded by a swappable model.

Features:
    US-KOR-02, F-12, ADR-04
"""

from collections.abc import Sequence
from typing import Protocol, runtime_checkable

type Vector = tuple[float, ...]
"""One embedding, sized by ``EmbeddingsSettings.dimensions``."""


@runtime_checkable
class EmbeddingsPort(Protocol):
    """Multilingual text embeddings; the model is named only in settings (ADR-04).

    Features:
        US-KOR-02, F-12, ADR-04
    """

    async def embed_query(self, text: str) -> Vector:
        """Embed a search query (a claim or a researcher's question).

        Args:
            text: The query text, already masked.

        Returns:
            The query vector.

        Raises:
            EmbeddingsUnavailableError: The provider failed after retries.
        """
        ...

    async def embed_documents(self, texts: Sequence[str]) -> list[Vector]:
        """Embed passages for indexing, one vector per text, in order.

        Args:
            texts: Passage texts.

        Returns:
            One vector per text.

        Raises:
            EmbeddingsUnavailableError: The provider failed after retries.
        """
        ...
