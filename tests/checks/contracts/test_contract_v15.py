"""Contract v15: CheckRequest carries image_id, with two image limitation codes (core#42).

Features:
    US-SPR-08, F-33, ADR-02
"""

from typing import get_args

import pytest
from pydantic import ValidationError

from meritum_core.checks import contracts as c
from meritum_core.checks.ocr import (
    ImageTooLargeError,
    UnsupportedImageError,
    UnsupportedImageFormatError,
)

IMAGE_ID = "image_" + "0" * 32


def test_image_alone_is_a_valid_request() -> None:
    request = c.CheckRequest.model_validate({"channel": "web", "image_id": IMAGE_ID})
    assert request.image_id == IMAGE_ID


@pytest.mark.parametrize(
    "other",
    [
        {"text": "Sejm przyjął ustawę"},
        {"url": "https://example.pl/a"},
        {"audio_id": "a"},
    ],
)
def test_image_excludes_text_url_and_audio(other: dict[str, str]) -> None:
    with pytest.raises(ValidationError, match="excludes"):
        c.CheckRequest.model_validate({"channel": "web", "image_id": IMAGE_ID} | other)


def test_request_without_any_input_is_still_rejected() -> None:
    with pytest.raises(ValidationError):
        c.CheckRequest.model_validate({"channel": "web"})


@pytest.mark.parametrize(
    ("error", "code"),
    [
        (UnsupportedImageFormatError, "image_format_unsupported"),
        (ImageTooLargeError, "image_too_large"),
    ],
)
def test_rejected_image_names_its_limitation_code(
    error: type[UnsupportedImageError], code: str
) -> None:
    assert error.limitation_code == code
    assert code in get_args(c.LimitationCode)
