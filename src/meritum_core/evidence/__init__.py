"""Evidence slice: citations, stance and evidence strength.

Public API of the domain: re-exports only.

Features:
    US-ZRD-01, F-16, ADR-06
"""

from meritum_core.evidence.citations import find_verbatim, verify_citation
from meritum_core.evidence.models import CitationDraft, SourceDocument

__all__ = ["CitationDraft", "SourceDocument", "find_verbatim", "verify_citation"]
