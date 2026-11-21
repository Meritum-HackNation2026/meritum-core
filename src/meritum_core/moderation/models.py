"""Models of the moderation slice that are not check contracts.

Features:
    US-MOD-05, F-20, F-25
"""

from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

from meritum_core.checks.contracts import StaffRole
from meritum_core.moderation.constants import (
    EMAIL_MAX_CHARS,
    EMAIL_PATTERN,
    KEYWORD_MAX_CHARS,
    TOPIC_NAME_MAX_CHARS,
)

type StaffEmail = Annotated[
    str,
    StringConstraints(
        strip_whitespace=True,
        to_lower=True,
        max_length=EMAIL_MAX_CHARS,
        pattern=EMAIL_PATTERN,
    ),
]
"""A staff address, stripped and lower-cased so lookups ignore case."""


class HighRiskTopic(BaseModel):
    """One topic of the admin's high-risk list, with its fallback keywords.

    A case whose claim falls under the topic gets the ``high_risk`` reason; the
    keywords classify it when the model cannot.

    Attributes:
        name: the topic, as ``ModeratorCase.high_risk_topic`` names it.
        keywords: the words that mark a claim as this topic.

    Features:
        US-MOD-05, F-20
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    name: Annotated[str, Field(min_length=1, max_length=TOPIC_NAME_MAX_CHARS)]
    keywords: Annotated[
        list[Annotated[str, Field(min_length=1, max_length=KEYWORD_MAX_CHARS)]],
        Field(min_length=1),
    ]


class StaffAccount(BaseModel):
    """A panel role an administrator granted to an e-mail address.

    Attributes:
        email: the address the OIDC provider must confirm (and verify).
        role: the role in the moderator panel.

    Features:
        US-MOD-05, F-25
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    email: StaffEmail
    role: StaffRole
