"""Fixtures for the OCR tests: images in a blob store, recorded Vision replies."""

import asyncio
import json
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Protocol

import httpx2
import pytest
from google.oauth2.credentials import Credentials

from meritum_core.checks.ocr import OcrPort, OcrSettings, build_ocr
from meritum_core.shared.blobs import BlobKind, BlobStore
from meritum_core.shared.blobs.adapters import MemoryBlobStore

FIXTURES = Path(__file__).parent

type Replies = list[tuple[int, str]]
type Sent = list[httpx2.Request]


class VisionFactory(Protocol):
    """Builds Vision on recorded replies; the retries default to one."""

    def __call__(self, replies: Replies, retries: int = 1) -> tuple[OcrPort, Sent]: ...


@pytest.fixture
def blobs() -> BlobStore:
    return MemoryBlobStore()


@pytest.fixture
def image_id(blobs: BlobStore) -> Callable[[str], str]:
    """Store a fixture image (or raw bytes for unknown names) and return its id."""

    def store(name: str) -> str:
        path = FIXTURES / name
        data = path.read_bytes() if path.exists() else name.encode()
        expires_at = datetime.now(UTC) + timedelta(hours=1)
        ref = asyncio.run(
            blobs.put(
                data,
                kind=BlobKind.IMAGE,
                content_type="application/octet-stream",
                expires_at=expires_at,
            )
        )
        return ref.blob_id

    return store


@pytest.fixture
def recorded_vision(blobs: BlobStore) -> VisionFactory:
    """Build Vision through the factory; each HTTP call gets the next reply."""

    def build(replies: Replies, retries: int = 1) -> tuple[OcrPort, Sent]:
        sent: Sent = []

        def reply(request: httpx2.Request) -> httpx2.Response:
            status, name = replies[min(len(sent), len(replies) - 1)]
            sent.append(request)
            payload = json.loads((FIXTURES / name).read_text(encoding="utf-8"))
            return httpx2.Response(status, json=payload)

        client = httpx2.AsyncClient(transport=httpx2.MockTransport(reply))
        token = Credentials(token="recorded")  # ruff: ignore[hardcoded-password-func-arg]  # fake token, no network
        settings = OcrSettings(
            provider="vision", project="meritum-test", retries=retries
        )
        vision = build_ocr(settings, blobs, credentials=token, http_client=client)
        return vision, sent

    return build
