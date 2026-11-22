"""What a corpus search returns, and what the corpus keeps about a legal act.

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


class LegalActMeta(BaseModel):
    """What ELI says about the legal act a corpus document holds.

    Internal to the corpus, not part of the checks contract. Field names are
    agreed on meritum-worker#162, the same as the worker's ingestion record.

    Attributes:
        eli: The act's ELI, such as ``DU/1997/483``.
        document_type: ELI ``type``: ``Ustawa``, ``Rozporządzenie``, ``Obwieszczenie``.
        legal_status: ELI ``status``: ``obowiązujący``, ``akt jednorazowy`` and so on.
        in_force: ELI ``inForce`` is ``IN_FORCE``.
        in_force_from: ELI ``validFrom``, else ``entryIntoForce``; None if absent.
        in_force_until: ELI ``expirationDate``; None for an act still in force.
        journal_publisher: ``DU`` (Dziennik Ustaw) or ``MP`` (Monitor Polski).
        journal_year: The journal's year.
        journal_position: The position in that year's journal.
        display_address: The citation, such as ``Dz.U. 1997 nr 78 poz. 483``.

    Features:
        US-KOR-02, US-ZRD-05, F-12
    """

    model_config = ConfigDict(frozen=True)

    eli: str = Field(min_length=1)
    document_type: str
    legal_status: str
    in_force: bool
    in_force_from: date | None
    in_force_until: date | None
    journal_publisher: str
    journal_year: int
    journal_position: int
    display_address: str
