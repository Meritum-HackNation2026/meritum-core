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
    "eval_run_done",  # staff: an evaluation run the recipient started finished
]
# A step of the check pipeline, shown in the processing strip and named by a
# check_progress notification; the text is analysis.steps.<code> in copy/pl.json.
AnalysisStepCode = Literal[
    "receive",
    "fetch_url",
    "transcribe_audio",
    "screen_injection",
    "extract_claims",
    "search_corpus",
    "search_web",
    "search_fact_checks",
    "assess_evidence",
    "verify_citations",
    "write_answer",
    "save_record",
]
# What a system notification says; text from copy/pl.json, never free (ADR-29).
SystemMessageCode = Literal[
    "maintenance_planned", "service_degraded", "service_restored"
]

# Why a check ended in technical_failure; never names a key or a provider.
FailureCode = Literal[
    "provider_unavailable",
    "web_search_unavailable",
    "transcription_failed",
    "url_unavailable",
    "not_ready",
]
# What a check could not cover; each code pairs with one text in limitations.
# A limitation never changes the check's status. corpus_scope: a note on what the
# corpus holds; no_publications: neither the corpus nor search found coverage.
# The audio codes explain an out_of_scope recording: unsupported format, or over
# the length or size limit.
LimitationCode = Literal[
    "fact_check_unavailable",
    "image_search_not_run",
    "audio_format_unsupported",
    "audio_too_long",
    "corpus_scope",
    "no_publications",
]
# Why a check is out_of_scope; the channel picks the text from copy/pl.json. audio is
# one value for any rejected recording: the detail (format, length) stays in
# limitation_codes, so the same fact is not stated twice.
OutOfScopeCode = Literal["image", "audio", "not_informational"]
# What would change the verdict, computed by a rule from the premises (US-ZRD-11).
VerdictChange = Literal[
    "needs_primary_source",
    "needs_second_publisher",
    "needs_fresh_evidence",
    "needs_resolving_source",
    "needs_named_source",
]
# What an incident match agreed on; a content match needs title, topic and date.
MatchBasis = Literal["title", "topic", "date", "domain"]
# Whether an incident matched the claim's content or the checked URL's domain.
MatchedOn = Literal["content", "domain"]
# Networks whose signatories' ClaimReview ratings may be premises (ADR-34).
FactCheckNetwork = Literal["ifcn", "efcsn"]

# Case outcome of an evaluation run, from the worst (US-OBS-04).
EvalOutcome = Literal["wrong_decisive", "non_verdict", "wrong_abstention", "correct"]
# golden: the repo's golden set; user_file: a case file a staff user uploaded.
EvalCaseSet = Literal["golden", "user_file"]
EvalRunStatus = Literal["queued", "running", "done", "failed"]
