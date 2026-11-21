"""Vertex AI adapter: Pydantic AI's Google embedding model, named only in settings.

Features:
    US-KOR-02, F-12, ADR-04, ADR-14
"""

from collections.abc import Awaitable, Sequence

from google.auth.credentials import Credentials
from google.auth.exceptions import GoogleAuthError
from google.genai.types import HttpRetryOptions
from httpx2 import AsyncClient
from pydantic_ai.embeddings import Embedder, EmbeddingResult, EmbeddingSettings
from pydantic_ai.embeddings.google import GoogleEmbeddingModel
from pydantic_ai.exceptions import ModelAPIError
from pydantic_ai.providers.google_cloud import GoogleCloudProvider

from meritum_core.shared.embeddings.errors import EmbeddingsUnavailableError
from meritum_core.shared.embeddings.ports import Vector
from meritum_core.shared.embeddings.settings import EmbeddingsSettings


class VertexEmbeddings:
    """EmbeddingsPort on a Vertex AI embedding model (queries and documents typed).

    Args:
        settings: Validated vertex settings (model and EU region are set).
        credentials: Google credentials; Application Default Credentials when None.
        http_client: HTTP client to use; tests pass one with a recorded reply.

    Features:
        US-KOR-02, F-12, ADR-04, ADR-14
    """

    def __init__(
        self,
        settings: EmbeddingsSettings,
        *,
        credentials: Credentials | None = None,
        http_client: AsyncClient | None = None,
    ) -> None:
        provider = GoogleCloudProvider(
            project=settings.project,
            location=settings.region,
            credentials=credentials,
            http_client=http_client,
            retry_options=HttpRetryOptions(attempts=settings.retries),
        )
        model = GoogleEmbeddingModel(
            settings.model,
            provider=provider,
            settings=EmbeddingSettings(dimensions=settings.dimensions),
        )
        self._embedder = Embedder(model)

    async def embed_query(self, text: str) -> Vector:
        """Embed a query with the model's retrieval-query task type.

        Args:
            text: The query text.

        Returns:
            The query vector.
        """
        (vector,) = _vectors(await self._call(self._embedder.embed_query(text)), 1)
        return vector

    async def embed_documents(self, texts: Sequence[str]) -> list[Vector]:
        """Embed passages with the model's retrieval-document task type.

        Args:
            texts: Passage texts.

        Returns:
            One vector per text.
        """
        result = await self._call(self._embedder.embed_documents(texts))
        return _vectors(result, len(texts))

    @staticmethod
    async def _call(pending: Awaitable[EmbeddingResult]) -> EmbeddingResult:
        try:
            return await pending
        except (ModelAPIError, GoogleAuthError) as exc:
            msg = "vertex embeddings failed after retries"
            raise EmbeddingsUnavailableError(msg) from exc


def _vectors(result: EmbeddingResult, expected: int) -> list[Vector]:
    vectors = [tuple(vector) for vector in result.embeddings]
    if len(vectors) != expected:
        msg = f"vertex returned {len(vectors)} vectors for {expected} texts"
        raise EmbeddingsUnavailableError(msg)
    return vectors
