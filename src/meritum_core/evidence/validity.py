"""Validity of each piece of evidence, set from metadata at the claim date (ADR-25).

The rule is deterministic: the stance step only supplies metadata from the corpus
and catalogue. Evidence that a newer piece replaced by the claim date is
``superseded``: it stays on the timeline but never counts towards strength or
conflict, so it cannot create a false disagreement.

Features:
    US-ZRD-05, US-ZRD-10, F-15, ADR-25
"""

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date

from meritum_core.checks.contracts import Citation, Validity


@dataclass(frozen=True, slots=True)
class EvidenceFacts:
    """A verified citation with the metadata its validity is set from.

    Attributes:
        citation: The verified citation.
        entry_validity: The ``validity`` of its catalogue entry; None when unknown.
        series: The publisher's series (e.g. one warning or bulletin thread);
            a newer document of the same publisher and series replaces older ones.
        past_event: Whether the evidence is explicitly about a single past event.
        repealed_on: When the cited act was repealed or amended, if it was.
        corrected: Whether the publisher explicitly corrected or withdrew it.

    Features:
        US-ZRD-05, US-ZRD-10, F-15, ADR-25
    """

    citation: Citation
    entry_validity: Validity | None = None
    series: str | None = None
    past_event: bool = False
    repealed_on: date | None = None
    corrected: bool = False


def assign_validity(
    evidence: Sequence[EvidenceFacts], *, claim_date: date
) -> list[Citation]:
    """Set ``Citation.validity`` for each piece of evidence at the claim date.

    Superseded: an explicit correction, an act repealed or amended on or before the
    claim date, or a newer document of the same publisher and series published by
    the end of the claim date. Otherwise ``past_event`` for evidence about a single
    past event, else the catalogue entry's validity (``expires`` when unknown).

    Args:
        evidence: The citations with their metadata.
        claim_date: The date the claim refers to.

    Returns:
        The citations, in the same order, with their validity set.

    Features:
        US-ZRD-05, US-ZRD-10, F-15, ADR-25
    """
    return [
        e.citation.model_copy(update={"validity": _validity(e, evidence, claim_date)})
        for e in evidence
    ]


def _validity(
    facts: EvidenceFacts, evidence: Sequence[EvidenceFacts], claim_date: date
) -> Validity:
    repealed = facts.repealed_on is not None and facts.repealed_on <= claim_date
    if facts.corrected or repealed or _replaced(facts, evidence, claim_date):
        return "superseded"
    if facts.past_event:
        return "past_event"
    return facts.entry_validity or "expires"


def _replaced(
    facts: EvidenceFacts, evidence: Sequence[EvidenceFacts], claim_date: date
) -> bool:
    published = facts.citation.source.published_at
    if facts.series is None or published is None:
        return False
    return any(
        other.series == facts.series
        and other.citation.source.publisher_id == facts.citation.source.publisher_id
        and (newer := other.citation.source.published_at) is not None
        and published < newer
        and newer.date() <= claim_date
        for other in evidence
    )
