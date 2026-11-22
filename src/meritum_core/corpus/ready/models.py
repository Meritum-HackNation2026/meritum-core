"""What the gold layer stores per chunk and what a gold search hit carries.

Features:
    US-KOR-02, US-ZRD-05, F-12
"""

from datetime import date
from enum import StrEnum
from typing import Self

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, model_validator


class DocumentKind(StrEnum):
    """Kind of the document a gold chunk comes from.

    Features:
        US-KOR-02, US-ZRD-05, F-12
    """

    ACT = "act"
    CONSOLIDATED_TEXT = "consolidated_text"
    DRAFT = "draft"
    NEWS = "news"
    STATEMENT = "statement"
    PAGE = "page"


class NumberTag(BaseModel):
    """A number the chunk states, with its unit and period (metadata, not citable).

    Attributes:
        value: The number as written, such as ``4806``.
        unit: Its unit, such as ``zł``, ``%``.
        period: The period it applies to, such as ``2026``; None when not stated.

    Features:
        US-ZRD-05, F-12
    """

    model_config = ConfigDict(frozen=True)

    value: str = Field(min_length=1)
    unit: str
    period: str | None = None


class GoldChunk(BaseModel):
    """One retrieval-ready chunk: citable text with a pointer back to bronze.

    ``text`` is exactly ``full_text[start_offset:end_offset]`` of the bronze
    document with ``checksum``; ``header`` is context for search only and is
    never citable. LLM output may only fill the metadata fields.

    Attributes:
        chunk_id: Stable id within its document version.
        source_id: The bronze ``corpus.documents`` row.
        checksum: The bronze ``checksum`` the offsets refer to.
        start_offset: First character in the bronze ``full_text``.
        end_offset: One past the last character.
        text: The citable text.
        header: Title, journal position, date, kind, status and chapter.
        kind: The document kind.
        published_on: Publication date of the document.
        valid_from: First day in force (acts, worker#162 ``in_force_from``).
        valid_to: Last day in force (``in_force_until``); None while in force.
        eli: The act's ELI, None for other documents.
        subject: Institution or subject the text is about.
        topic: Short topic label.
        numbers: Numbers with unit and period.
        summary: One-sentence summary (metadata).
        weight: Base weight set by the builder (title-only stubs rank low).

    Features:
        US-KOR-02, US-ZRD-05, F-12
    """

    model_config = ConfigDict(frozen=True)

    chunk_id: str = Field(min_length=1)
    source_id: str = Field(min_length=1)
    checksum: str = Field(min_length=1)
    start_offset: int = Field(ge=0)
    end_offset: int
    text: str = Field(min_length=1)
    header: str
    kind: DocumentKind
    published_on: date | None = None
    valid_from: date | None = None
    valid_to: date | None = None
    eli: str | None = None
    subject: str | None = None
    topic: str | None = None
    numbers: tuple[NumberTag, ...] = ()
    summary: str | None = None
    weight: float = Field(default=1.0, gt=0, le=1)

    @model_validator(mode="after")
    def _offsets_span_the_text(self) -> Self:
        if self.end_offset - self.start_offset != len(self.text):
            msg = "end_offset - start_offset must equal len(text)"
            raise ValueError(msg)
        return self


class GoldHit(BaseModel):
    """A gold chunk found by one ranking, with what its weight needs.

    Attributes:
        chunk_id: The chunk's id.
        source_id: Its bronze document.
        text: The citable text.
        published_on: Publication date.
        fetched_at: When bronze fetched the document.
        kind: The document kind.
        valid_from: First day in force.
        valid_to: Last day in force.
        weight: The builder's base weight.

    Features:
        US-KOR-02, US-ZRD-05, F-12
    """

    model_config = ConfigDict(frozen=True)

    chunk_id: str
    source_id: str
    text: str
    published_on: date | None
    fetched_at: AwareDatetime
    kind: DocumentKind
    valid_from: date | None
    valid_to: date | None
    weight: float
