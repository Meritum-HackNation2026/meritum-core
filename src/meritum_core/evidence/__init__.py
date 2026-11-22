"""Evidence slice: citations, stance and evidence strength.

Public API of the domain: re-exports only.

Features:
    US-ZRD-01, US-ZRD-03, US-ZRD-04, US-ZRD-05, US-ZRD-10, US-ZRD-11, US-KOR-01,
    F-14, F-15, F-16, F-17, ADR-05, ADR-06, ADR-24, ADR-25, ADR-34
"""

from meritum_core.evidence.citations import find_verbatim, verify_citation
from meritum_core.evidence.claim_reviews import (
    normalize_rating,
    rate_review,
    rating_stance,
)
from meritum_core.evidence.dating import outdated_verdict, resolve_claim_date
from meritum_core.evidence.models import (
    CitationDraft,
    FoundClaimReview,
    RatedReview,
    SourceDocument,
)
from meritum_core.evidence.strength import (
    compute_premises,
    compute_strength,
    settle_verdict,
)
from meritum_core.evidence.validity import EvidenceFacts, assign_validity
from meritum_core.evidence.verdict_changes import compute_verdict_changes

__all__ = [
    "CitationDraft",
    "EvidenceFacts",
    "FoundClaimReview",
    "RatedReview",
    "SourceDocument",
    "assign_validity",
    "compute_premises",
    "compute_strength",
    "compute_verdict_changes",
    "find_verbatim",
    "normalize_rating",
    "outdated_verdict",
    "rate_review",
    "rating_stance",
    "resolve_claim_date",
    "settle_verdict",
    "verify_citation",
]
