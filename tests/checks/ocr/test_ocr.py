"""OcrPort: Vision on recorded replies, the stub, the factory, format checks."""

import asyncio
import json
from collections.abc import Callable
from datetime import date
from pathlib import Path

import pytest
from pydantic import ValidationError
from tests.checks.ocr.conftest import VisionFactory

from meritum_core.checks.ocr import (
    ImageTooLargeError,
    OcrPort,
    OcrSettings,
    OcrUnavailableError,
    UnsupportedImageFormatError,
    build_image_search,
    build_ocr,
    find_date,
    inspect_image,
)
from meritum_core.checks.ocr.constants import MAX_IMAGE_BYTES, VISION_ENDPOINT
from meritum_core.shared.blobs import BlobNotFoundError, BlobStore

type StoreImage = Callable[[str], str]


def test_vision_reads_text_and_date_candidate(
    recorded_vision: VisionFactory, image_id: StoreImage
) -> None:
    vision, sent = recorded_vision([(200, "annotate-reply.json")])
    result = asyncio.run(vision.read(image_id("pixel.png")))
    assert result.text.startswith("Pilne! Sejm przyjął ustawę")
    assert result.claim_date == date(2026, 11, 12)
    assert result.date_confirms_publication is False
    assert result.metadata.format == "png"
    assert str(sent[0].url) == VISION_ENDPOINT
    request = json.loads(sent[0].content)["requests"][0]
    assert request["features"] == [{"type": "DOCUMENT_TEXT_DETECTION"}]


def test_image_without_text_gives_empty_text(
    recorded_vision: VisionFactory, image_id: StoreImage
) -> None:
    vision, _ = recorded_vision([(200, "annotate-empty.json")])
    result = asyncio.run(vision.read(image_id("pixel.png")))
    assert (result.text, result.claim_date) == ("", None)


@pytest.mark.parametrize(
    "reply", [(503, "unavailable.json"), (200, "annotate-error.json")]
)
def test_provider_failure_is_unavailable(
    recorded_vision: VisionFactory, image_id: StoreImage, reply: tuple[int, str]
) -> None:
    vision, sent = recorded_vision([reply], 2)
    with pytest.raises(OcrUnavailableError) as raised:
        asyncio.run(vision.read(image_id("pixel.png")))
    assert raised.value.check_status == "technical_failure"
    assert len(sent) == (2 if reply[0] == 503 else 1)


def test_unsupported_format_never_leaves_the_process(
    recorded_vision: VisionFactory, image_id: StoreImage
) -> None:
    vision, sent = recorded_vision([(200, "annotate-reply.json")])
    with pytest.raises(UnsupportedImageFormatError) as raised:
        asyncio.run(vision.read(image_id("zdjecie.xyz")))
    assert raised.value.check_status == "out_of_scope"
    assert sent == []


def test_oversized_image_is_rejected() -> None:
    with pytest.raises(ImageTooLargeError):
        inspect_image(b"\x89PNG\r\n\x1a\n" + bytes(MAX_IMAGE_BYTES))


def test_find_date_skips_impossible_dates() -> None:
    assert find_date("31.02.2026 i potem 3/4/2026") == date(2026, 4, 3)
    assert find_date("bez daty 12.2026") is None


def test_stub_reads_its_text_without_provider_keys(
    blobs: BlobStore,
    image_id: StoreImage,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    text = tmp_path / "ocr.txt"
    text.write_text("Post z 12.11.2026", encoding="utf-8")
    monkeypatch.setenv("MERITUM_OCR_STUB_TEXT", str(text))
    stub = build_ocr(OcrSettings(), blobs)
    result = asyncio.run(stub.read(image_id("pixel.png")))
    assert result.claim_date == date(2026, 11, 12)


def test_stub_without_text_fails_as_unavailable(
    blobs: BlobStore, image_id: StoreImage
) -> None:
    stub = build_ocr(OcrSettings(), blobs)
    with pytest.raises(OcrUnavailableError, match="fixture"):
        asyncio.run(stub.read(image_id("pixel.png")))


def test_missing_image_raises_blob_not_found(blobs: BlobStore) -> None:
    stub = build_ocr(OcrSettings(), blobs)
    with pytest.raises(BlobNotFoundError):
        asyncio.run(stub.read("image_" + "0" * 32))


def test_factory_builds_vision_and_it_needs_a_project(blobs: BlobStore) -> None:
    vision = build_ocr(OcrSettings(provider="vision", project="meritum-test"), blobs)
    assert isinstance(vision, OcrPort)
    assert type(vision).__name__ == "VisionOcr"
    with pytest.raises(ValidationError):
        OcrSettings(provider="vision")


def test_image_search_says_it_did_not_search() -> None:
    result = asyncio.run(build_image_search().search("image_" + "0" * 32))
    assert (result.searched, result.occurrences) == (False, [])
