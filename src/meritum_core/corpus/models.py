"""What a corpus search returns.

Features:
    US-KOR-02, US-ZRD-05, F-12
"""

from datetime import date

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field


class Passage(BaseModel):
    """One passage of a source document, with the dates freshness is judged by.

    Attributes:
        passage_id: Stable id of the passage in the corpus.
        source_id: Id of the catalogued source document it comes from.
        text: The passage text (source text: data, never instructions).
        published_on: Publication date of the document, None when unknown.
        fetched_at: When the document was fetched.
        score: Fused, freshness-weighted score; 0 before fusion.

    Features:
        US-KOR-02, US-ZRD-05, F-12
    """

    model_config = ConfigDict(frozen=True)

    passage_id: str = Field(min_length=1)
    source_id: str = Field(min_length=1)
    text: str
    published_on: date | None
    fetched_at: AwareDatetime
    score: float = Field(default=0.0, ge=0)
