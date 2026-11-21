"""Constants of the checks slice: input normalization, contracts and verdict rules.

The contract value sets are typed with the contract literals; those annotations are
only read by type checkers, so importing the contracts here creates no runtime cycle.

Features: US-WTY-03, F-05, ADR-19, ADR-02
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Final

if TYPE_CHECKING:
    from meritum_core.checks.contracts import (
        Channel,
        MatchBasis,
        MatchedOn,
        NotificationKind,
        Stance,
        Validity,
        Verdict,
    )

NORMALIZATION_VERSION: Final = 1
"""Version of the normalization rules; part of every result-cache key.

Raise it whenever the rules change, so entries keyed by the old rules are never hit.
"""

TRACKING_PARAMS: Final = frozenset(
    {
        "fbclid",
        "gclid",
        "igshid",
        "mc_cid",
        "mc_eid",
        "ref",
        "ref_src",
        "s",
        "si",
    }
)
"""Query parameters that only track the sharer and never identify the post."""

TRACKING_PREFIXES: Final = ("utm_",)
"""Prefixes of tracking query parameters (``utm_source``, ``utm_medium``...)."""

QUOTES: Final = {
    **dict.fromkeys(
        "\u201e\u201c\u201d\u00ab\u00bb\u201f\u2033\u301d\u301e\uff02", '"'
    ),
    **dict.fromkeys("\u201a\u2018\u2019\u2039\u203a\u201b\u2032\uff07`", "'"),
}
"""Typographic quotes (\u201e \u201d \u00ab \u2019 ...) and their ASCII form."""

DASHES: Final = dict.fromkeys(
    "\u2010\u2011\u2012\u2013\u2014\u2015\u2212\ufe58\ufe63\uff0d", "-"
)
"""Hyphens, dashes and minus signs, all written as ``-``."""

URL_PATTERN: Final = re.compile(r"https?://\S+", re.IGNORECASE)
"""An http(s) URL inside pasted text; it runs until the next whitespace."""

WHITESPACE: Final = re.compile(r"\s+")
"""Any run of Unicode whitespace, non-breaking spaces and newlines included."""

URL_TRAILING_PUNCTUATION: Final = ".,;:!?)\"'"
"""Characters that end a sentence after a pasted URL and are not part of it."""

URL_SCHEMES: Final = frozenset({"http", "https"})
"""Schemes a post URL may have; anything else is dropped from the context."""

CONTRACT_VERSION: Final = 5
"""Version of the check contracts (CheckRequest, CheckResult, ...).

Independent of the job contract version in meritum_core.jobs.contracts. Raise it on
any change that breaks a consumer, and regenerate (scripts/generate-contracts.sh).
"""

MIN_TEXT_CHARS: Final = 3
"""Fewest non-blank characters a text-only CheckRequest must carry (US-SPR-01)."""

STRONG_MIN_SOURCES: Final = 2
"""Agreeing independent publishers for a strong or moderate verdict (US-ZRD-03)."""

SETTLING: Final[frozenset[Verdict]] = frozenset({"confirmed", "false", "misleading"})
"""Verdicts that settle a claim: only they need citations and have a strength."""

AGREEING_STANCE: Final[dict[Verdict, Stance]] = {
    "confirmed": "supports",
    "false": "refutes",
    "misleading": "context",
}
"""The stance that agrees with each settling verdict; only those citations count."""

PER_EVIDENCE_VALIDITY: Final[frozenset[Validity]] = frozenset(
    {
        "past_event",
        "superseded",
    }
)
"""Validities set per piece of evidence, never for a whole catalogue entry."""

DEFAULT_MAX_AGE_HOURS: Final = 365 * 24
"""Age after which expiring evidence is archival, unless its catalogue says less."""

SESSIONLESS_CHANNELS: Final[frozenset[Channel]] = frozenset({"discord", "sms", "mcp"})
"""Channels with no browser session: their session id is the hashed channel user id."""

CHECK_KINDS: Final[frozenset[NotificationKind]] = frozenset(
    {
        "check_progress",
        "check_done",
        "new_evidence",
    }
)
"""Notification kinds that name the check they are about."""

CASE_KINDS: Final[frozenset[NotificationKind]] = frozenset(
    {
        "moderator_answer",
        "case_assigned",
    }
)
"""Notification kinds that name the moderator case they are about."""

REQUIRED_MATCH_BASIS: Final[dict[MatchedOn, frozenset[MatchBasis]]] = {
    "content": frozenset({"title", "topic", "date"}),
    "domain": frozenset({"domain", "topic"}),
}
"""What an incident match must agree on; a domain alone never makes a content match."""
