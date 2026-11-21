"""Constants of the moderation slice.

Features:
    US-MOD-05, F-20, F-25
"""

from typing import Final

TOPIC_NAME_MAX_CHARS: Final = 80
"""Longest high-risk topic name; equals ``ModeratorCase.high_risk_topic``'s limit."""

KEYWORD_MAX_CHARS: Final = 80
"""Longest keyword of a high-risk topic (the fallback classifier matches them)."""

CASE_WRITE_LOCK: Final = 74_0001
"""PostgreSQL advisory lock key taken by every case write, so a save racing a
check removal waits for it and then sees the removed checks (core#74)."""

EMAIL_MAX_CHARS: Final = 254
"""Longest staff e-mail address (RFC 5321 path limit)."""

EMAIL_PATTERN: Final = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"
"""Shape of a staff address: one ``@`` and a dotted domain; the provider proves it."""
