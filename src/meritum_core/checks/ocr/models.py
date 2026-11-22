"""Models of OCR: what an image is and what the ports return.

Features:
    US-SPR-08, F-33, ADR-30
"""

from datetime import date
from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class ImageFormat(StrEnum):
    """Image formats the port accepts, recognised from the file's bytes.

    Features:
        US-SPR-08, F-33, ADR-30
    """

    PNG = "png"
    JPEG = "jpeg"
    WEBP = "webp"


class ImageInfo(BaseModel):
    """File metadata learnt from the bytes, handed on as context for the claim.

    Attributes:
        format: The image format.
        size_bytes: The file size.

    Features:
        US-SPR-08, F-33, ADR-30
    """

    model_config = ConfigDict(frozen=True)

    format: ImageFormat
    size_bytes: int = Field(ge=0)


class OcrResult(BaseModel):
    """Text read from an image, checked like any other text afterwards.

    Attributes:
        text: The recognised text; empty when the image holds none.
        claim_date: The first date written in the text, a candidate for
            ``claim_date``; None when there is none.
        date_confirms_publication: Always False: a date visible on an image
            does not prove when the post was really published.
        metadata: Format and size of the file.

    Features:
        US-SPR-08, F-33, ADR-30
    """

    model_config = ConfigDict(frozen=True)

    text: str
    claim_date: date | None = None
    date_confirms_publication: Literal[False] = False
    metadata: ImageInfo


class ImageOccurrence(BaseModel):
    """An earlier appearance of the image found by a search.

    Attributes:
        url: Where the image appeared before.
        seen_on: When it was seen there, if known.

    Features:
        US-SPR-08, F-33, ADR-30
    """

    model_config = ConfigDict(frozen=True)

    url: str = Field(min_length=1)
    seen_on: date | None = None


class ImageSearchResult(BaseModel):
    """What an earlier-occurrence search found, or that it did not run.

    Attributes:
        searched: False when no search API or local image base is configured;
            the answer then tells the user nothing was searched.
        occurrences: Earlier appearances; always empty when not searched.

    Features:
        US-SPR-08, F-33, ADR-30
    """

    model_config = ConfigDict(frozen=True)

    searched: bool
    occurrences: list[ImageOccurrence] = []
