"""Claim context that never changes the verdict: incidents, ratings, sanctions.

Features:
    US-ZRD-07, US-ZRD-08, ADR-02
"""

from __future__ import annotations

from datetime import datetime
from typing import Annotated, Literal

from pydantic import Field, HttpUrl, model_validator

from meritum_core.checks.constants import CONTENT_MATCH_BASIS

from ._base import _Model
from ._types import MatchBasis


class IncidentMatch(_Model):
    """Similarity to a known incident (organiser's database, the local EUvsDisinfo copy or a checked fact-check). Context only.

    Never a basis for the verdict by itself, and never changes it. An EUvsDisinfo `fact` text is cited as a Citation,
    not carried here.

    `domain` is the one explicitly defined warning case: the checked URL is on a domain the incident database lists
    (for EUvsDisinfo: linksToDisinformation), and the incident's topic matches the claim. A content match needs a
    matching title, topic and date; the domain alone never makes one. `match_basis` lists what matched and is shown.

    Attributes:
        database: the incident database that matched.
        incident_id: the incident's id in that database.
        matched_on: whether the content or the domain matched.
        match_basis: what agreed between the claim and the incident.
        title: the incident title.
        date: the incident date.
        url: the incident link.
        similarity: the similarity score from 0 to 1.

    Features:
        US-ZRD-08, ADR-02
    """

    database: Annotated[
        Literal["organiser", "euvsdisinfo", "fact_check"],
        Field(
            description="fact_check: the entry matched an already checked publication."
        ),
    ] = "organiser"
    incident_id: Annotated[str, Field(min_length=1, max_length=80)]
    matched_on: Literal["content", "domain"] = "content"
    match_basis: Annotated[
        list[MatchBasis],
        Field(min_length=1, description="What agreed; shown with the match."),
    ]
    title: Annotated[str, Field(max_length=200)]
    date: datetime
    url: HttpUrl
    similarity: Annotated[float, Field(ge=0, le=1)]

    @model_validator(mode="after")
    def _content_needs_title_topic_date(self) -> IncidentMatch:
        is_content = self.matched_on == "content"
        if is_content and not CONTENT_MATCH_BASIS.issubset(self.match_basis):
            raise ValueError("a content match needs a matching title, topic and date")
        return self


class ClaimReviewContext(_Model):
    """A fact-checker's ClaimReview rating found through Google Fact Check Tools API, shown as context with a link.

    Never a citation, never counted towards strength, kept no longer than the API's cache headers allow.

    Attributes:
        publisher: the fact-checker's name.
        rating: the textualRating as published.
        url: the fact-check link.
        reviewed_at: when the claim was reviewed, when known.

    Features:
        US-KOR-01, ADR-24, ADR-02
    """

    publisher: Annotated[str, Field(min_length=2, max_length=120)]
    rating: Annotated[
        str,
        Field(min_length=1, max_length=120, description="textualRating as published."),
    ]
    url: HttpUrl
    reviewed_at: datetime | None = None


class SourceStatusWarning(_Model):
    """Neutral note that the checked content comes from an entity on the official EU sanctions list. Never a verdict.

    Attributes:
        code: the warning code.
        entity: the sanctioned entity's name.
        basis_url: the link to the sanctions list entry.

    Features:
        US-ZRD-07, ADR-02
    """

    code: Literal["eu_sanctioned_entity"]
    entity: Annotated[str, Field(max_length=120)]
    basis_url: HttpUrl
