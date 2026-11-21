"""The input every channel adapter sends to the verification core.

Features:
    US-SPR-01, US-WTY-08, US-BEZ-05, US-BEZ-06, ADR-02
"""

from __future__ import annotations

from typing import Annotated

from pydantic import Field, HttpUrl, model_validator

from meritum_core.checks.constants import MIN_TEXT_CHARS, SESSIONLESS_CHANNELS

from ._base import _Model
from ._types import Channel


class CheckRequest(_Model):
    """What a channel adapter sends to the verification core. The core is channel-agnostic.

    Attributes:
        channel: the channel the request came through.
        text: the text to check, up to 4000 characters.
        url: a link to check.
        page_url: extension only, the post the text came from.
        audio_id: an uploaded audio file or Discord voice message.
        channel_user_id: Discord, SMS and MCP only, the user id in that channel. The API
            turns it into the salted channel_user_hash (backend/027) and never stores it.
        session_id: web and extension only, the random browser session id that the
            API copies to CheckRecord.session_id.

    Features:
        US-SPR-01, US-SPR-07, US-SPR-11, US-WTY-01, US-WTY-02, US-WTY-06,
        US-WTY-07, US-WTY-08, US-WTY-09, US-BEZ-02, US-BEZ-05, US-BEZ-06, ADR-02
    """

    channel: Channel
    text: Annotated[str | None, Field(max_length=4000)] = None
    url: HttpUrl | None = None
    page_url: Annotated[
        HttpUrl | None,
        Field(description="Extension only: the post the text came from."),
    ] = None
    audio_id: Annotated[
        str | None,
        Field(
            min_length=1,
            max_length=80,
            description="Uploaded audio file or Discord voice message; transcribed in an EU region, then checked like text.",
        ),
    ] = None
    channel_user_id: Annotated[
        str | None,
        Field(
            min_length=1,
            max_length=128,
            description="Discord, SMS and MCP only: user id, phone number or MCP client id. The API hashes it with a salt into channel_user_hash and never stores it.",
        ),
    ] = None
    session_id: Annotated[
        str | None,
        Field(
            min_length=8,
            max_length=64,
            description="Web and extension only: random id kept in the browser session; the API copies it to CheckRecord.session_id.",
        ),
    ] = None

    @model_validator(mode="after")
    def _text_url_or_audio(self) -> CheckRequest:
        has_text = self.text is not None and len(self.text.strip()) >= MIN_TEXT_CHARS
        if self.url is None and self.audio_id is None and not has_text:
            raise ValueError("send text (3+ characters), a URL or an audio file")
        return self

    @model_validator(mode="after")
    def _channel_user_id_only_when_sessionless(self) -> CheckRequest:
        sessionless = self.channel in SESSIONLESS_CHANNELS
        if self.channel_user_id is not None and not sessionless:
            raise ValueError(
                "only Discord, SMS and MCP requests carry a channel user id"
            )
        if self.session_id is not None and sessionless:
            raise ValueError("Discord, SMS and MCP requests carry no session id")
        return self
