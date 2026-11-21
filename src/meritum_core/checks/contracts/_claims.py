"""One checked claim with its verdict, citations and strength.

Features:
    US-SPR-03, US-SPR-04, ADR-02
"""

from __future__ import annotations

from datetime import date
from typing import Annotated

from pydantic import Field, model_validator

from ._base import _Model
from ._context import ClaimReviewContext, IncidentMatch
from ._sources import Citation, ClaimReviewPremise
from ._strength import EvidenceStrength
from ._types import ClaimDateSource, TechniqueCode, Verdict, VerdictChange
from ._verdict_rules import check_verdict_rules


class ClaimResult(_Model):
    """One checked claim. Citations (source material) are kept apart from `explanation` (model interpretation).

    Attributes:
        claim: the claim as extracted.
        claim_date: the date the claim refers to; always set, evidence age counts from it.
        claim_date_source: where the claim date was taken from.
        verdict: the verdict on the claim.
        strength: the evidence strength of a settling verdict.
        citations: the source fragments behind the verdict.
        claim_review_premises: fact-checkers' ClaimReview ratings behind the verdict.
        explanation: the model's interpretation of the citations.
        unresolved: what could not be established.
        would_change_verdict: what evidence would change the verdict, as codes.
        archival: whether the newest evidence is older than the claim needs.
        technique: the manipulation technique a misleading claim uses.
        incident: a known incident the claim resembles.
        claim_reviews: fact-checkers' ratings shown as context.

    Features:
        US-SPR-03, US-SPR-04, US-SPR-05, US-ZRD-02, US-ZRD-04, US-ZRD-05,
        US-ZRD-06, US-ZRD-08, US-ZRD-11, US-KOR-01, F-14, ADR-02, ADR-34
    """

    claim: Annotated[str, Field(min_length=5, max_length=500)]
    claim_date: Annotated[
        date,
        Field(
            description="The date the claim refers to; evidence age is measured against it."
        ),
    ]
    claim_date_source: ClaimDateSource
    verdict: Verdict
    strength: EvidenceStrength | None = None
    citations: list[Citation] = []
    claim_review_premises: Annotated[
        list[ClaimReviewPremise],
        Field(
            description="IFCN or EFCSN fact-checkers' ratings that back the verdict without a page fragment (ADR-34)."
        ),
    ] = []
    explanation: Annotated[str, Field(min_length=10, max_length=800)]
    unresolved: Annotated[
        str | None, Field(max_length=500, description="What could not be established.")
    ] = None
    would_change_verdict: Annotated[
        list[VerdictChange],
        Field(
            description="What would change the verdict, computed by a rule from the premises; the channel words it from copy/pl.json."
        ),
    ] = []
    archival: Annotated[
        bool,
        Field(description="Newest evidence is older than the claim's context needs."),
    ] = False
    technique: TechniqueCode | None = None
    incident: IncidentMatch | None = None
    claim_reviews: list[ClaimReviewContext] = []

    @model_validator(mode="after")
    def _verdict_rules(self) -> ClaimResult:
        check_verdict_rules(self)
        return self
