"""Code lists of the check contracts: the literal types every model shares.

Features:
    ADR-02
"""

from typing import Annotated, Literal

from pydantic import Field

Channel = Literal["web", "extension", "discord", "sms", "mcp"]

Verdict = Literal[
    "confirmed", "false", "misleading", "insufficient_evidence", "not_verifiable"
]

# Outcomes that are not verdicts and must be shown separately (MSZ section 2 and 5).
CheckStatus = Literal[
    "done", "needs_clarification", "out_of_scope", "technical_failure"
]

SourceKind = Literal[
    "akt_prawny", "dane_publiczne", "instytucja", "fact_check", "media"
]
# primary: official documents and public data; secondary: fact-checkers (media only if
# the catalogue admits them).
SourceTier = Literal["primary", "secondary"]
# How the document reached the corpus; mcp: the local EUvsDisinfo copy synced through
# its MCP server.
SourceVia = Literal["corpus", "rss", "web_search", "mcp"]
Stance = Literal["supports", "refutes", "context"]
Agreement = Literal["consistent", "conflicting"]
# Overrides of the age rule. expires: age counts; in_force: e.g. a legal act in force;
# updated_in_place: standing official guidance edited in place (passenger rights,
# contact pages); past_event: evidence explicitly about a past event; superseded: newer
# evidence replaced it by the claim date, so it neither conflicts nor counts towards
# strength.
Validity = Literal[
    "expires", "in_force", "updated_in_place", "past_event", "superseded"
]
Strength = Literal["strong", "moderate", "weak"]
# Where the claim date comes from: a date in the checked text, the publication date of
# the input (e.g. the post), or today.
ClaimDateSource = Literal["text", "input_published_at", "today"]
PublisherId = Annotated[str, Field(pattern=r"^[a-z0-9][a-z0-9-]{1,79}$")]

TechniqueCode = Literal[
    "false_authority",
    "conspiracy_theory",
    "out_of_context",
    "outdated",
    "fabricated_quote",
    "manipulated_media",
    "impersonation",
    "cherry_picking",
]

CacheableStatus = Literal["done", "needs_clarification", "out_of_scope"]

# repeated_unanswered: the second similar unanswered claim from anyone, in any channel.
# user_dispute: „Zgłoś błąd”.
CaseReason = Literal[
    "insufficient_evidence", "high_risk", "repeated_unanswered", "user_dispute"
]
StaffRole = Literal[
    "moderator", "analyst", "admin"
]  # admin manages staff accounts and the high-risk topic list

NotificationKind = Literal[
    "check_progress",  # a long check moved on (audio, queue)
    "check_done",
    "moderator_answer",  # a moderator answered a case the recipient's check joined
    "new_evidence",  # new evidence for an earlier question
    "case_assigned",  # staff: a case was created or updated for the moderator
    "system",
]
