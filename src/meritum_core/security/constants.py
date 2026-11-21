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
    r"(?<![\w+])"
    r"(?P<prefix>(?:\+|00)48[ -]?)?"
    r"(?P<digits>\d{3}[ -]?\d{3}[ -]?\d{3}|\d{2}[ -]?\d{3}[ -]?\d{2}[ -]?\d{2})"
    r"(?!\w)"
)
"""Polish phone: optional +48/0048, 9 digits as 3-3-3 (mobile) or 2-3-2-2 (landline),
groups split by spaces or hyphens. A match without the prefix may be an amount;
``AMOUNT_HEAD_PATTERN`` and ``AMOUNT_TAIL_PATTERN`` decide (#102)."""

AMOUNT_HEAD_PATTERN: Final = re.compile(
    r"(?:(?<!\d[ \u00a0.-])(?<!\d)\d{1,3}(?P<separator>[ \u00a0.-])|[$€])$"
)
"""Text right before a phone-shaped match that makes it part of an amount: one
leading digit group and a thousands separator ("1 450 000 000") or a currency sign
("$850 000 000"). The separator must be the one inside the match, so
"lokal 12 601-234-567" stays a phone; a second group before it ("601 234 567 601 234
567") means two phones, not one 18-digit amount."""

AMOUNT_HEAD_WINDOW: Final = 4
"""Characters before a phone-shaped match that ``AMOUNT_HEAD_PATTERN`` reads."""

AMOUNT_UNITS: Final = (
    "zł",
    "złotych",
    "PLN",
    "EUR",
    "euro",
    "USD",
    "€",
    "$",
    "osób",
    "tys.",
    "mln",
    "mld",
)
"""Words and signs after a number that make it an amount or a count, not a phone."""

AMOUNT_TAIL_PATTERN: Final = re.compile(
    r"(?:,\d|\s*(?i:" + "|".join(map(re.escape, AMOUNT_UNITS)) + r")(?!\w))"
)
"""Text right after a phone-shaped match that makes it an amount: decimals or a unit.

Fixed alternatives after optional spaces, so the check takes linear time."""

EMAIL_PATTERN: Final = re.compile(r"(?<![\w.+-])[\w.+-]+@[\w-]+(?:\.[\w-]+)+")
"""E-mail address: local part, @, a domain with at least one dot.

A match starts only at a token start, so long input takes linear time."""

PESEL_PATTERN: Final = re.compile(r"(?<![\w+])\d{11}(?!\w)")
"""Candidate PESEL: exactly 11 digits; the checksum decides."""

PESEL_WEIGHTS: Final = (1, 3, 7, 9, 1, 3, 7, 9, 1, 3)
"""Weights of the first ten PESEL digits in the checksum."""
