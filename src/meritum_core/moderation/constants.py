"""Constants of the moderation slice.

Features:
    US-MOD-05, F-20
"""

from typing import Final

TOPIC_NAME_MAX_CHARS: Final = 80
"""Longest high-risk topic name; equals ``ModeratorCase.high_risk_topic``'s limit."""

KEYWORD_MAX_CHARS: Final = 80
"""Longest keyword of a high-risk topic (the fallback classifier matches them)."""
