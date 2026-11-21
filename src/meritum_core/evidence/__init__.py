"""Evidence slice: citations, stance and evidence strength.

Public API of the domain: re-exports only.

Features:
    US-ZRD-01, US-ZRD-03, US-ZRD-04, US-ZRD-05, US-ZRD-10, US-ZRD-11, F-15,
    F-16, F-17, ADR-05, ADR-06, ADR-25
"""

from meritum_core.evidence.citations import find_verbatim, verify_citation
from meritum_core.evidence.dating import outdated_verdict, resolve_claim_date
from meritum_core.evidence.models import CitationDraft, SourceDocument
from meritum_core.evidence.strength import (
    compute_premises,
    compute_strength,
    settle_verdict,
)
from meritum_core.evidence.verdict_changes import compute_verdict_changes
from meritum_core.evidence.validity import EvidenceFacts, assign_validity

__all__ = [
    "CitationDraft",
    "EvidenceFacts",
    "SourceDocument",
    "assign_validity",
    "compute_premises",
    "compute_strength",
    "compute_verdict_changes",
    "find_verbatim",
    "outdated_verdict",
    "resolve_claim_date",
    "settle_verdict",
    "verify_citation",
]
