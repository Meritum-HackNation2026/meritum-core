"""Inputs of the verbatim citation check and of the ClaimReview rating rule.

Features:
    US-ZRD-01, US-KOR-01, F-14, F-16, ADR-06, ADR-34
"""

from dataclasses import dataclass
from datetime import datetime

from pydantic import BaseModel, ConfigDict, HttpUrl

from meritum_core.checks.contracts import (
    ClaimReviewContext,
    ClaimReviewPremise,
    FactCheckNetwork,
    PublisherId,
    Source,
    Stance,
    Validity,
)


class CitationDraft(BaseModel):
    """A citation as the model returns it, before the verbatim check.

    Only the source id, fragment, stance and validity are read; any title,
    publisher, date or link the model adds is ignored (``extra="ignore"``).

    Attributes:
        source_id: The id of the cited document in the corpus.
        fragment: The fragment the model claims to quote (untrusted).
        stance: Whether the fragment supports, refutes or gives context.
        validity: The age rule the model set for this piece of evidence.

    Features:
        US-ZRD-01, F-16, ADR-06
    """

    model_config = ConfigDict(frozen=True, extra="ignore")

    source_id: str
    fragment: str
    stance: Stance
    validity: Validity = "expires"


@dataclass(frozen=True, slots=True)
class SourceDocument:
    """A corpus document as the database holds it: metadata and full text.

    Attributes:
        source: Title, publisher, date and link from the database.
        text: The full source text the fragment must occur in (data, never
            instructions).

    Features:
        US-ZRD-01, F-16, ADR-06
    """

    source: Source
    text: str


class FoundClaimReview(BaseModel):
    """A ClaimReview rating as Fact Check Tools API returned it, before the rating rule.

    Attributes:
        publisher: The fact-checker's name as shown.
        publisher_id: The catalogue publisher id; independence is counted on it.
        signatory_of: The networks the catalogue lists the publisher in.
        rating: The textualRating, verbatim (untrusted).
        title: The fact-check's title.
        reviewed_at: When the claim was reviewed.
        url: The fact-check link.
        fetched_at: When the API returned the rating.

    Features:
        US-KOR-01, F-14, ADR-24, ADR-34
    """

    model_config = ConfigDict(frozen=True)

    publisher: str
    publisher_id: PublisherId
    signatory_of: list[FactCheckNetwork]
    rating: str
    title: str
    reviewed_at: datetime
    url: HttpUrl
    fetched_at: datetime


@dataclass(frozen=True, slots=True)
class RatedReview:
    """A fact-checker's rating after the rating rule, with how long it may be kept.

    Attributes:
        evidence: A premise of the verdict, or context with a link when the rating
            is not in the publisher's table or the publisher is no signatory.
        keep_until: The end of the retention the API's cache headers allow (ADR-24).

    Features:
        US-KOR-01, F-14, ADR-24, ADR-34
    """

    evidence: ClaimReviewPremise | ClaimReviewContext
    keep_until: datetime
