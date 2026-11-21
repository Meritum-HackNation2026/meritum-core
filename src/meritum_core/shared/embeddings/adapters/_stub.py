"""Stub embeddings: hashed word stems, deterministic, no keys and no network.

Features:
    US-KOR-02, F-12, ADR-04
"""

import math
import re
from collections.abc import Sequence
from hashlib import blake2b

from meritum_core.shared.embeddings.constants import STUB_STEM_LENGTH
from meritum_core.shared.embeddings.ports import Vector


class StubEmbeddings:
    """Bag of word stems hashed into ``dimensions`` buckets, L2-normalised.

    Args:
        dimensions: Vector size.

    Features:
        US-KOR-02, F-12, ADR-04
    """

    def __init__(self, dimensions: int) -> None:
        self._dimensions = dimensions

    async def embed_query(self, text: str) -> Vector:
        """Embed one text.

        Args:
            text: Any text.

        Returns:
            Its vector; all zeros when the text has no words.
        """
        return self._embed(text)

    async def embed_documents(self, texts: Sequence[str]) -> list[Vector]:
        """Embed each text.

        Args:
            texts: Any texts.

        Returns:
            One vector per text.
        """
        return [self._embed(text) for text in texts]

    def _embed(self, text: str) -> Vector:
        counts = [0.0] * self._dimensions
        for word in re.findall(r"\w+", text.lower()):
            digest = blake2b(word[:STUB_STEM_LENGTH].encode(), digest_size=8).digest()
            counts[int.from_bytes(digest) % self._dimensions] += 1.0
        norm = math.sqrt(math.fsum(c * c for c in counts)) or 1.0
        return tuple(c / norm for c in counts)
