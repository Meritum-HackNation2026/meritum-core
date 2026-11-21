"""Patterns and markers of the personal-data masking (security/pii).

Features:
    US-BEZ-04, F-20, ADR-13
"""

import re
from typing import Final

PHONE_MARKER: Final = "[telefon]"
"""Replaces a Polish phone number."""

EMAIL_MARKER: Final = "[e-mail]"
"""Replaces an e-mail address."""

PESEL_MARKER: Final = "[PESEL]"
"""Replaces a PESEL number with a valid checksum."""

PHONE_PATTERN: Final = re.compile(
    r"(?<![\w+])(?<!\d[ -])"  # not the tail of a longer number
    r"(?:(?:\+|00)48[ -]?)?"
    r"(?:\d{3}[ -]?\d{3}[ -]?\d{3}|\d{2}[ -]?\d{3}[ -]?\d{2}[ -]?\d{2})"
    r"(?![ -]?\d)(?!\w)"
)
"""Polish phone: optional +48/0048, 9 digits as 3-3-3 (mobile) or 2-3-2-2 (landline),
groups split by spaces or hyphens."""

EMAIL_PATTERN: Final = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")
"""E-mail address: local part, @, a domain with at least one dot."""

PESEL_PATTERN: Final = re.compile(r"(?<![\w+])\d{11}(?!\w)")
"""Candidate PESEL: exactly 11 digits; the checksum decides."""

PESEL_WEIGHTS: Final = (1, 3, 7, 9, 1, 3, 7, 9, 1, 3)
"""Weights of the first ten PESEL digits in the checksum."""
