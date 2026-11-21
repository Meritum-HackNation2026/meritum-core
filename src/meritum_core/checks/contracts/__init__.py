"""Meritum contracts: the data every Meritum surface renders (MSZ "Prawdowid").

This package is the single source of truth. `scripts/export_contracts.py` writes `contracts/meritum.schema.json`
and `contracts/meritum.ts`; the design system and the TypeScript apps consume those generated files.
User-facing strings live in `copy/pl.json`; this file carries codes, not copy.

Rules from the MSZ brief that the models enforce:
- a verdict that settles a claim (confirmed, false, misleading) needs at least one citation and explicit premises;
  only such a verdict has a strength;
- the strength of a verdict follows from the premises by a fixed rule, never from the model's say-so;
- agreement follows from the citation stances; conflicting credible sources give "insufficient_evidence" with both sides cited and no strength;
- conflict is computed only between evidence valid at the claim date: evidence that newer evidence replaced (superseded) is shown
  on the timeline but neither conflicts nor counts towards strength;
- independence is counted per catalogue publisher (publisher_id), not per page or domain, and only among citations whose
  stance agrees with the verdict;
- evidence age is measured against the date the claim refers to (claim_date), with a per-catalogue-entry threshold; evidence
  that does not expire (a legal act in force, an official page updated in place, evidence about a past event) is never archival;
- insufficient evidence says what could not be established;
- technical failure, a request for clarification and out-of-scope input are not verdicts and carry no claims;
- every factual claim gets a verdict: "out_of_scope" is only for an unsupported input type or a request that is not about
  information, "needs_clarification" only when no claim can be extracted;
- recommending a hand-off to a moderator is distinct from creating a case;
- an incident match (organiser's database or EUvsDisinfo) and the domain warning are context and never change the verdict;
- Discord, SMS and MCP have no browser session: their session_id is the salted hash of the channel user id;
- the result cache keeps only the substantive part of a result and never a technical failure; escalation is computed per request.
"""

from meritum_core.checks.constants import (
    AGREEING_STANCE,
    CASE_KINDS,
    CHECK_KINDS,
    CONTRACT_VERSION,
    DEFAULT_MAX_AGE_HOURS,
    MIN_TEXT_CHARS,
    PER_EVIDENCE_VALIDITY,
    SESSIONLESS_CHANNELS,
    SETTLING,
    STRONG_MIN_SOURCES,
)

from ._claims import ClaimResult
from ._context import ClaimReviewContext, IncidentMatch, SourceStatusWarning
from ._moderation import CaseClaim, ModeratorCase
from ._notifications import Notification
from ._progress import AnalysisStatus, AnalysisStep
from ._records import CheckRecord, InjectionEvent, ModelUsage
from ._request import CheckRequest
from ._results import CachedResult, CheckResult, Escalation
from ._sources import CatalogEntry, Citation, Source
from ._strength import EvidenceStrength, Premises, is_stale, strength_for
from ._types import (
    Agreement,
    CacheableStatus,
    CaseReason,
    Channel,
    CheckStatus,
    ClaimDateSource,
    NotificationKind,
    PublisherId,
    SourceKind,
    SourceTier,
    SourceVia,
    StaffRole,
    Stance,
    Strength,
    TechniqueCode,
    Validity,
    Verdict,
)

__all__ = [
    "AGREEING_STANCE",
    "CASE_KINDS",
    "CHECK_KINDS",
    "CONTRACT_VERSION",
    "DEFAULT_MAX_AGE_HOURS",
    "MIN_TEXT_CHARS",
    "PER_EVIDENCE_VALIDITY",
    "SESSIONLESS_CHANNELS",
    "SETTLING",
    "STRONG_MIN_SOURCES",
    "Agreement",
    "AnalysisStatus",
    "AnalysisStep",
    "CacheableStatus",
    "CachedResult",
    "CaseClaim",
    "CaseReason",
    "CatalogEntry",
    "Channel",
    "CheckRecord",
    "CheckRequest",
    "CheckResult",
    "CheckStatus",
    "Citation",
    "ClaimDateSource",
    "ClaimResult",
    "ClaimReviewContext",
    "Escalation",
    "EvidenceStrength",
    "IncidentMatch",
    "InjectionEvent",
    "ModelUsage",
    "ModeratorCase",
    "Notification",
    "NotificationKind",
    "Premises",
    "PublisherId",
    "Source",
    "SourceKind",
    "SourceStatusWarning",
    "SourceTier",
    "SourceVia",
    "StaffRole",
    "Stance",
    "Strength",
    "TechniqueCode",
    "Validity",
    "Verdict",
    "is_stale",
    "strength_for",
]
