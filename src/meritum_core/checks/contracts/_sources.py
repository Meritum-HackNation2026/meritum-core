"""Sources from the audited corpus, the citations cut from them and the source catalogue.

Features:
    US-ZRD-01, US-ZRD-12, US-KOR-01, ADR-02
"""

from __future__ import annotations

from datetime import datetime
from typing import Annotated, Literal

from pydantic import Field, HttpUrl, model_validator

from meritum_core.checks.constants import PER_EVIDENCE_VALIDITY

from ._base import _Model
from ._types import PublisherId, SourceKind, SourceTier, SourceVia, Stance, Validity


class Source(_Model):
    """A document from the audited corpus. Title, publisher, date and link are mandatory to show (MSZ section 2).

    Attributes:
        id: the document id in the corpus.
        title: the document title.
        publisher: the publisher's name as shown.
        publisher_id: the catalogue publisher id; independence is counted on it.
        url: the document link.
        domain: the catalogue domain the document comes from.
        kind: the kind of source.
        tier: primary (official) or secondary (fact-checkers).
        published_at: the publication date, when known.
        fetched_at: when the document was fetched.
        language: the two-letter language code.
        via: how the document reached the corpus.

    Features:
        US-ZRD-01, US-KOR-02, US-KOR-03, US-KOR-04, US-KOR-06, ADR-02
    """

    id: Annotated[str, Field(min_length=1, max_length=80)]
    title: Annotated[str, Field(min_length=3, max_length=200)]
    publisher: Annotated[str, Field(min_length=2, max_length=120)]
    publisher_id: Annotated[
        PublisherId,
        Field(
            description="Publisher id from the catalogue; independence is counted on it."
        ),
    ]
    url: HttpUrl
    domain: Annotated[str, Field(min_length=3, max_length=100)]
    kind: SourceKind
    tier: SourceTier
    published_at: datetime | None = None
    fetched_at: datetime
    language: Annotated[str, Field(pattern=r"^[a-z]{2}$")] = "pl"
    via: SourceVia = "corpus"


class Citation(_Model):
    """A fragment of a source and how it bears on the claim. The pipeline drops fragments it cannot find verbatim.

    Attributes:
        source: the cited document.
        fragment: the verbatim fragment.
        stance: whether the fragment supports, refutes or gives context.
        validity: the age rule for this piece of evidence.
        fragment_found_verbatim: always true; unverified fragments are dropped.

    Features:
        US-ZRD-01, US-ZRD-05, US-ZRD-09, US-ZRD-10, ADR-02
    """

    source: Source
    fragment: Annotated[str, Field(min_length=10, max_length=600)]
    stance: Stance
    validity: Annotated[
        Validity,
        Field(
            description="Age rule for this piece of evidence: the catalogue entry's validity, or past_event / superseded set per evidence."
        ),
    ] = "expires"
    fragment_found_verbatim: Literal[True] = True


class CatalogEntry(_Model):
    """One domain in the open source catalogue: why it qualifies, how it is refreshed, whether it is excluded.

    Attributes:
        domain: the catalogue domain.
        publisher: the publisher's name.
        publisher_id: the publisher id independence is counted on.
        kind: the kind of source.
        tier: primary or secondary.
        license: the licence the content is used under.
        ingest: how documents of the domain are ingested.
        refresh_hours: how often the domain is refreshed.
        validity: the age override for every document of the entry.
        max_age_hours: a shorter threshold for short-lived sources.
        qualified_because: why the domain qualifies.
        tdm_reservation: the owner's text and data mining opt-out.
        excluded: whether the domain is excluded.
        exclusion_reason: why it is excluded.

    Features:
        US-ZRD-12, US-KOR-01, US-KOR-05, US-KOR-08, ADR-02
    """

    domain: Annotated[str, Field(min_length=3, max_length=100)]
    publisher: Annotated[str, Field(min_length=2, max_length=120)]
    publisher_id: PublisherId
    kind: SourceKind
    tier: SourceTier
    license: Annotated[str, Field(min_length=2, max_length=120)]
    ingest: Annotated[
        Literal["static", "rss", "sitemap", "web_search", "mcp", "api"],
        Field(
            description="mcp: the local EUvsDisinfo copy; api: Google Fact Check Tools, used only to discover URLs and show the rating as context."
        ),
    ]
    refresh_hours: Annotated[int | None, Field(ge=1)] = None
    validity: Annotated[
        Validity,
        Field(
            description="Age override for every document of this entry; past_event and superseded are set per evidence."
        ),
    ] = "expires"
    max_age_hours: Annotated[
        int | None,
        Field(
            ge=1,
            description="Shorter threshold for short-lived sources (warnings, roads, weather: hours or days).",
        ),
    ] = None
    qualified_because: Annotated[str, Field(min_length=10, max_length=300)]
    tdm_reservation: Annotated[
        Literal["none", "reserved", "unknown"],
        Field(
            description="Machine-readable text and data mining opt-out (robots.txt incl. Content-Signal, meta tags, tdmrep), checked per domain."
        ),
    ] = "unknown"
    excluded: bool = False
    exclusion_reason: Annotated[str | None, Field(max_length=300)] = None

    @model_validator(mode="after")
    def _exclusion_has_reason(self) -> CatalogEntry:
        if self.excluded and (
            self.exclusion_reason is None or not self.exclusion_reason
        ):
            raise ValueError("an excluded source needs a reason")
        if self.validity in PER_EVIDENCE_VALIDITY:
            raise ValueError(
                f"{self.validity!r} describes one piece of evidence, not a whole catalogue entry"
            )
        reserved = self.tdm_reservation == "reserved"
        if self.tier == "secondary" and reserved and not self.excluded:
            raise ValueError(
                "a secondary source whose owner reserved text and data mining is excluded"
            )
        if self.validity != "expires" and self.max_age_hours is not None:
            raise ValueError("a source that does not expire has no maximum age")
        return self
