"""EmbeddingsPort: the stub is deterministic and offline; Vertex is picked by settings."""

import asyncio
import math

import pytest
from pydantic import ValidationError

from meritum_core.shared.embeddings import (
    EmbeddingsPort,
    EmbeddingsSettings,
    build_embeddings,
)


def stub(dimensions: int = 64) -> EmbeddingsPort:
    return build_embeddings(EmbeddingsSettings(provider="stub", dimensions=dimensions))


def cosine(a: tuple[float, ...], b: tuple[float, ...]) -> float:
    return sum(x * y for x, y in zip(a, b, strict=True))


def test_stub_is_deterministic_normalized_and_sized() -> None:
    first = asyncio.run(stub().embed_query("Ostrzeżenie meteorologiczne"))
    again = asyncio.run(stub().embed_query("Ostrzeżenie meteorologiczne"))
    assert first == again
    assert len(first) == 64
    assert math.isclose(math.fsum(x * x for x in first), 1.0)


def test_stub_embeds_documents_one_vector_each() -> None:
    vectors = asyncio.run(stub(8).embed_documents(["a b", "c d", "e"]))
    assert [len(v) for v in vectors] == [8, 8, 8]


def test_stub_gives_inflected_forms_close_vectors() -> None:
    port = stub()
    query = asyncio.run(port.embed_query("ostrzeżenie meteorologiczne"))
    near, far = asyncio.run(
        port.embed_documents(["Ostrzeżenia meteorologiczne", "Ceny paliw"])
    )
    assert cosine(query, near) > cosine(query, far)


def test_stub_text_without_words_is_a_zero_vector() -> None:
    assert set(asyncio.run(stub(4).embed_query("?!"))) == {0.0}


def test_vertex_needs_an_eu_region() -> None:
    with pytest.raises(ValidationError, match="REGION"):
        EmbeddingsSettings(provider="vertex")
    with pytest.raises(ValidationError, match="EU region"):
        EmbeddingsSettings(provider="vertex", model="m", region="us-central1")


def test_settings_come_from_the_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MERITUM_EMBEDDINGS_PROVIDER", "vertex")
    monkeypatch.setenv("MERITUM_EMBEDDINGS_MODEL", "gemini-embedding-001")
    monkeypatch.setenv("MERITUM_EMBEDDINGS_REGION", "europe-west4")
    settings = EmbeddingsSettings()
    assert (settings.provider, settings.model) == ("vertex", "gemini-embedding-001")


def test_vertex_defaults_to_gemini_embedding_001() -> None:
    settings = EmbeddingsSettings(provider="vertex", region="europe-west4")
    assert settings.model == "gemini-embedding-001"
