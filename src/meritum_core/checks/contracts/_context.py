"""Context next to a claim that never changes its verdict: incidents, ratings, sanctions.

Features:
    US-ZRD-07, US-ZRD-08, ADR-02
"""

from datetime import datetime
from typing import Annotated, Literal

from pydantic import Field, HttpUrl

from ._base import _Model


class IncidentMatch(_Model):
    """Similarity to a known incident (organiser's database or the local EUvsDisinfo copy). Context only.

    Never a basis for the verdict by itself, and never changes it. An EUvsDisinfo `fact` text is cited as a Citation,
    not carried here.

    `domain` is the one explicitly defined warning case: the checked URL is on a domain the incident database lists
    (for EUvsDisinfo: linksToDisinformation), and the incident's topic matches the claim.

    Attributes:
        database: the incident database that matched.
        incident_id: the incident's id in that database.
        matched_on: whether the content or the domain matched.
        title: the incident title.
        date: the incident date.
        url: the incident link.
        similarity: the similarity score from 0 to 1.

    Features:
        US-ZRD-08, ADR-02
    """

    database: Literal["organiser", "euvsdisinfo"] = "organiser"
    incident_id: Annotated[str, Field(min_length=1, max_length=80)]
    matched_on: Literal["content", "domain"] = "content"
    title: Annotated[str, Field(max_length=200)]
    date: datetime
    url: HttpUrl
    similarity: Annotated[float, Field(ge=0, le=1)]


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
