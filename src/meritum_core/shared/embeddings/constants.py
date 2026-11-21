"""Constants of the embeddings port.

Features:
    US-KOR-02, F-12, ADR-04
"""

from typing import Final

ENV_PREFIX: Final = "MERITUM_EMBEDDINGS_"
"""Prefix of every embeddings setting in the environment (ADR-04)."""

DEFAULT_MODEL: Final = "gemini-embedding-001"
"""Vertex AI model when ``MERITUM_EMBEDDINGS_MODEL`` is unset (ADR-04); adapters
never name a model, they take it from settings."""

DEFAULT_REGION: Final = "europe-central2"
"""Vertex AI location when ``MERITUM_EMBEDDINGS_REGION`` is unset: Warsaw, in the
EU (ADR-14) and serving ``DEFAULT_MODEL``; the choice is explained in the README."""

DEFAULT_DIMENSIONS: Final = 768
"""Vector size; must match ``vector(768)`` in the corpus migrations (pgvector HNSW
indexes at most 2000 dimensions, gemini-embedding-001 gives 3072 unless reduced)."""

DEFAULT_RETRIES: Final = 3
"""HTTP attempts per call, the first included, before EmbeddingsUnavailableError."""

EU_REGIONS: Final = frozenset(
    {
        "eu",
        "europe-central2",
        "europe-north1",
        "europe-southwest1",
        "europe-west1",
        "europe-west3",
        "europe-west4",
        "europe-west8",
        "europe-west9",
    }
)
"""Vertex AI locations inside the EU (ADR-14); London and Zurich are not."""

STUB_STEM_LENGTH: Final = 5
"""The stub hashes each word's first letters, so Polish inflections of a word
("ostrzeżenie", "ostrzeżenia") land in the same dimension, as a real model would."""
