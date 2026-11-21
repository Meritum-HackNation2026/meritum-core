"""The audit record of one check: question, time, sources, result, model usage.

Features:
    US-OBS-01, US-BEZ-01, ADR-02
"""

from __future__ import annotations

from datetime import datetime
from typing import Annotated, Literal

from pydantic import Field, HttpUrl, model_validator

from meritum_core.checks.constants import SESSIONLESS_CHANNELS

from ._base import _Model
from ._results import Escalation
from ._types import Channel, CheckStatus, Verdict


class ModelUsage(_Model):
    """One model call: provider, model, region of processing, tokens and cost.

    Attributes:
        provider: the model provider.
        model: the model name.
        region: where the data was processed.
        input_tokens: tokens sent.
        output_tokens: tokens received.
        cost_usd: the call's cost in US dollars.

    Features:
        US-OBS-02, ADR-02
    """

    provider: Annotated[str, Field(max_length=60)]
    model: Annotated[str, Field(max_length=80)]
    region: Annotated[
        str, Field(max_length=40, description="Where the data was processed.")
    ]
    input_tokens: Annotated[int, Field(ge=0)]
    output_tokens: Annotated[int, Field(ge=0)]
    cost_usd: Annotated[float, Field(ge=0)]


class InjectionEvent(_Model):
    """Instructions found in the input or a source. Logged and never executed.

    In user content the instruction is cut out and the rest is analysed as data; a catalogue source
    with an instruction drops out of the evidence.

    Attributes:
        location: the user input or a source.
        action: what was done with the instruction.
        source_url: the source that carried it, for source events.
        excerpt: the instruction found.

    Features:
        US-BEZ-01, ADR-02
    """

    location: Literal["input", "source"]
    action: Literal["instruction_removed", "source_dropped"]
    source_url: HttpUrl | None = None
    excerpt: Annotated[str, Field(max_length=300)]

    @model_validator(mode="after")
    def _action_follows_location(self) -> InjectionEvent:
        expected = (
            "instruction_removed" if self.location == "input" else "source_dropped"
        )
        if self.action != expected:
            raise ValueError(
                "an instruction in user input is cut out; a source with one is dropped"
            )
        if (self.location == "source") != (self.source_url is not None):
            raise ValueError(
                "a source event names the source URL, an input event does not"
            )
        return self


class CheckRecord(_Model):
    """Audit log of one check (MSZ MVP: question, time, sources, result; plus observability).

    Attributes:
        check_id: the check's id.
        session_id: the browser session, or the hashed channel user id.
        user_id: the signed-in user, if any.
        channel: the channel the check came through.
        channel_user_hash: Discord, SMS and MCP only, the salted user id hash.
        received_at: when the question arrived.
        answered_at: when the answer was sent.
        question_masked: the input with personal data masked.
        status: the check's status.
        verdicts: the verdict of each claim.
        source_ids: the ids of the cited sources.
        corpus_version: the corpus snapshot used.
        models: every model call of the check.
        web_search_calls: how many web searches ran.
        retrieval_errors: retrieval failures met on the way.
        injection_events: instructions found and neutralised.
        escalation: the hand-off to the moderator queue.
        cache_hit: whether the substantive part came from the result cache.
        retention_until: when the record is deleted.

    Features:
        US-SPR-10, US-BEZ-04, US-BEZ-05, US-BEZ-06, US-OBS-01, US-OBS-02,
        US-OBS-03, US-OBS-04, US-OBS-07, ADR-02
    """

    check_id: str
    session_id: Annotated[
        str,
        Field(
            min_length=8,
            max_length=64,
            description="Web and extension: random id kept in the browser session. Discord, SMS, MCP: the salted hash of the channel user id (equal to channel_user_hash).",
        ),
    ]
    user_id: Annotated[
        str | None,
        Field(
            min_length=8,
            max_length=64,
            description="Signed-in users only (Google or Microsoft account); None for anonymous checks.",
        ),
    ] = None
    channel: Channel
    channel_user_hash: Annotated[
        str | None,
        Field(
            pattern=r"^[0-9a-f]{64}$",
            description="Discord, SMS and MCP only: salted SHA-256 of the user id, phone number or MCP client id, used to reply and count repeats; never shown to moderators.",
        ),
    ] = None
    received_at: datetime
    answered_at: datetime
    question_masked: Annotated[
        str,
        Field(max_length=4000, description="Input with obvious personal data masked."),
    ]
    status: CheckStatus
    verdicts: list[Verdict]
    source_ids: list[str]
    corpus_version: str
    models: list[ModelUsage]
    web_search_calls: Annotated[int, Field(ge=0)] = 0
    retrieval_errors: list[Annotated[str, Field(max_length=200)]] = []
    injection_events: list[InjectionEvent] = []
    escalation: Escalation | None = None
    cache_hit: Annotated[
        bool,
        Field(
            description="Substantive part served from the result cache; escalation was still computed."
        ),
    ] = False
    retention_until: datetime

    @model_validator(mode="after")
    def _channel_identity(self) -> CheckRecord:
        sessionless = self.channel in SESSIONLESS_CHANNELS
        if sessionless != (self.channel_user_hash is not None):
            raise ValueError(
                "only Discord, SMS and MCP checks carry a hashed channel user id, and"
                " they always do"
            )
        hashed = self.channel_user_hash
        if hashed is not None and self.session_id != hashed:
            raise ValueError(
                "on Discord, SMS and MCP the session id is the hashed channel user id"
            )
        return self

    @property
    def latency_ms(self) -> int:
        """Time from receiving the question to answering it, in milliseconds."""
        return int((self.answered_at - self.received_at).total_seconds() * 1000)

    @property
    def cost_usd(self) -> float:
        """Total model cost of the check."""
        return sum(m.cost_usd for m in self.models)

    @property
    def abstained(self) -> bool:
        """Whether a finished check settled no claim."""
        return self.status == "done" and all(
            v in {"insufficient_evidence", "not_verifiable"} for v in self.verdicts
        )
