"""Vertex embeddings through the factory, answered by a recorded Vertex AI reply."""

import asyncio
import json

import httpx2
import pytest
from google.oauth2.credentials import Credentials

from meritum_core.shared.embeddings import (
    EmbeddingsPort,
    EmbeddingsSettings,
    EmbeddingsUnavailableError,
    build_embeddings,
)

RECORDED = {"predictions": [{"embeddings": {"values": [0.6, 0.8]}}]}
UNAVAILABLE = {"error": {"code": 503, "message": "down", "status": "UNAVAILABLE"}}


def vertex(
    status: int, sent: list[httpx2.Request], recorded: object = RECORDED
) -> EmbeddingsPort:
    def reply(request: httpx2.Request) -> httpx2.Response:
        sent.append(request)
        body = recorded if status == httpx2.codes.OK else UNAVAILABLE
        return httpx2.Response(status, json=body)

    settings = EmbeddingsSettings(
        provider="vertex",
        model="gemini-embedding-001",
        region="europe-west4",
        project="meritum-test",
        dimensions=2,
        retries=1,
    )
    client = httpx2.AsyncClient(transport=httpx2.MockTransport(reply), timeout=60)
    token = Credentials(token="recorded")  # ruff: ignore[hardcoded-password-func-arg]  # fake token, no network
    return build_embeddings(settings, credentials=token, http_client=client)


def test_query_uses_the_configured_model_region_and_dimensions() -> None:
    sent: list[httpx2.Request] = []
    vector = asyncio.run(vertex(200, sent).embed_query("burza"))
    assert vector == (0.6, 0.8)
    (request,) = sent
    assert "/locations/europe-west4/" in request.url.path
    assert request.url.path.endswith("/models/gemini-embedding-001:predict")
    body = json.loads(request.content)
    assert body["parameters"]["outputDimensionality"] == 2
    assert body["instances"][0]["task_type"] == "RETRIEVAL_QUERY"


def test_documents_use_the_document_task_type() -> None:
    sent: list[httpx2.Request] = []
    asyncio.run(vertex(200, sent).embed_documents(["burza"]))
    assert (
        json.loads(sent[0].content)["instances"][0]["task_type"] == "RETRIEVAL_DOCUMENT"
    )


def test_provider_failure_raises_embeddings_unavailable() -> None:
    with pytest.raises(EmbeddingsUnavailableError):
        asyncio.run(vertex(503, []).embed_query("burza"))


def test_wrong_number_of_vectors_raises_embeddings_unavailable() -> None:
    two = {"predictions": RECORDED["predictions"] * 2}
    with pytest.raises(EmbeddingsUnavailableError):
        asyncio.run(vertex(200, [], two).embed_query("burza"))
    with pytest.raises(EmbeddingsUnavailableError):
        asyncio.run(vertex(200, [], two).embed_documents(["a", "b", "c"]))
