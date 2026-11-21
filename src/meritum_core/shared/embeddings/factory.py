"""Builds the embeddings adapter named by ``MERITUM_EMBEDDINGS_PROVIDER``.

Features:
    US-KOR-02, F-12, ADR-04
"""

from google.auth.credentials import Credentials
from httpx2 import AsyncClient

from meritum_core.shared.embeddings.adapters import StubEmbeddings, VertexEmbeddings
from meritum_core.shared.embeddings.ports import EmbeddingsPort
from meritum_core.shared.embeddings.settings import (
    EmbeddingsProvider,
    EmbeddingsSettings,
)


def build_embeddings(
    settings: EmbeddingsSettings,
    *,
    credentials: Credentials | None = None,
    http_client: AsyncClient | None = None,
) -> EmbeddingsPort:
    """Build the adapter the settings name.

    Args:
        settings: Usually ``EmbeddingsSettings()`` from the environment.
        credentials: Google credentials for Vertex; Application Default
            Credentials when None. Ignored by the stub.
        http_client: HTTP client for Vertex (a recorded reply in tests).
            Ignored by the stub.

    Returns:
        The stub or the Vertex AI adapter.

    Features:
        US-KOR-02, F-12, ADR-04
    """
    match settings.provider:
        case EmbeddingsProvider.VERTEX:
            return VertexEmbeddings(
                settings, credentials=credentials, http_client=http_client
            )
        case EmbeddingsProvider.STUB:
            return StubEmbeddings(settings.dimensions)
