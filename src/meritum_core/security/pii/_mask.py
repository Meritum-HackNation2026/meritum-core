"""Masking of phone numbers, e-mails and PESEL numbers in free text.

Features:
    US-BEZ-04, F-20, ADR-13
"""

import re

from pydantic import BaseModel

from meritum_core.security.constants import (
    EMAIL_MARKER,
    EMAIL_PATTERN,
    PESEL_MARKER,
    PESEL_PATTERN,
    PESEL_WEIGHTS,
    PHONE_MARKER,
    PHONE_PATTERN,
)


class MaskedText(BaseModel, frozen=True):
    """Text with personal data replaced by markers; never holds the original.

    Attributes:
        text: the masked text.
        replaced: how many personal-data items were replaced.

    Features:
        US-BEZ-04, F-20, ADR-13
    """

    text: str
    replaced: int


def _valid_pesel(digits: str) -> bool:
    total = sum(int(d) * w for d, w in zip(digits, PESEL_WEIGHTS, strict=False))
    return (10 - total % 10) % 10 == int(digits[10])


def _pesel_or_keep(match: re.Match[str]) -> str:
    return PESEL_MARKER if _valid_pesel(match[0]) else match[0]


def mask_personal_data(text: str) -> MaskedText:
    """Replace phones, e-mails and checksum-valid PESEL numbers with markers.

    Idempotent: the markers contain no digits or ``@``, so masking twice
    changes nothing. Run it before a workflow starts and on step results.

    Args:
        text: free text that may contain personal data.

    Returns:
        The masked text and the number of replacements.

    Features:
        US-BEZ-04, F-20, ADR-13
    """
    masked = PESEL_PATTERN.sub(_pesel_or_keep, text)
    masked = EMAIL_PATTERN.sub(EMAIL_MARKER, masked)
    masked = PHONE_PATTERN.sub(PHONE_MARKER, masked)
    markers = (PHONE_MARKER, EMAIL_MARKER, PESEL_MARKER)
    # Count added markers only: markers already in the input are not new replacements.
    replaced = sum(masked.count(m) - text.count(m) for m in markers)
    return MaskedText(text=masked, replaced=replaced)
