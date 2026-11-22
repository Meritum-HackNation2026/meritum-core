"""Masking of personal data: the gate first, then the always-on patterns.

Features:
    US-BEZ-04, F-20, ADR-13, ADR-35
"""

import logging
import re

from meritum_core.security.constants import (
    AMOUNT_HEAD_PATTERN,
    AMOUNT_HEAD_WINDOW,
    AMOUNT_NEXT_GROUP_PATTERN,
    AMOUNT_TAIL_PATTERN,
    EMAIL_MARKER,
    EMAIL_PATTERN,
    ID_CARD_MARKER,
    ID_CARD_PATTERN,
    ID_CARD_WEIGHTS,
    PESEL_MARKER,
    PESEL_PATTERN,
    PESEL_WEIGHTS,
    PHONE_MARKER,
    PHONE_PATTERN,
)
from meritum_core.security.pii.errors import PiiGateUnavailableError
from meritum_core.security.pii.models import MaskedText
from meritum_core.security.pii.ports import PiiGatePort

_log = logging.getLogger(__name__)


def _valid_pesel(digits: str) -> bool:
    total = sum(int(d) * w for d, w in zip(digits[:10], PESEL_WEIGHTS, strict=True))
    return (10 - total % 10) % 10 == int(digits[10])


def _pesel_or_keep(match: re.Match[str]) -> str:
    return PESEL_MARKER if _valid_pesel(match[0]) else match[0]


def _id_card_or_keep(match: re.Match[str]) -> str:
    # int(c, 36) reads A as 10 ... Z as 35, the identity card letter values.
    values = [int(c, 36) for c in match[0]]
    total = sum(v * w for v, w in zip(values, ID_CARD_WEIGHTS, strict=True))
    return ID_CARD_MARKER if total % 10 == 0 else match[0]


def _is_amount(match: re.Match[str]) -> bool:
    if match["prefix"]:
        return False
    text, start, end = match.string, match.start(), match.end()
    separator = next((c for c in match["digits"] if not c.isdigit()), None)
    head = AMOUNT_HEAD_PATTERN.search(text, max(0, start - AMOUNT_HEAD_WINDOW), start)
    leading = head["separator"] if head else None  # None after a currency sign
    same_leading = not isinstance(leading, str) or leading == separator
    continues_a_number = head is not None and same_leading
    next_group = AMOUNT_NEXT_GROUP_PATTERN.match(text, end)
    following = next_group["separator"] if next_group else None
    ends_a_number = isinstance(following, str) and following == separator
    has_unit = AMOUNT_TAIL_PATTERN.match(text, end) is not None
    return continues_a_number or ends_a_number or has_unit


def _phone_or_keep(match: re.Match[str]) -> str:
    return match[0] if _is_amount(match) else PHONE_MARKER


def _mask_patterns(text: str) -> MaskedText:
    masked = PESEL_PATTERN.sub(_pesel_or_keep, text)
    masked = EMAIL_PATTERN.sub(EMAIL_MARKER, masked)
    masked = ID_CARD_PATTERN.sub(_id_card_or_keep, masked)
    masked = PHONE_PATTERN.sub(_phone_or_keep, masked)
    markers = (PHONE_MARKER, EMAIL_MARKER, PESEL_MARKER, ID_CARD_MARKER)
    # Count added markers only: markers already in the input are not new replacements.
    replaced = sum(masked.count(m) - text.count(m) for m in markers)
    return MaskedText(text=masked, replaced=replaced)


async def mask_personal_data(text: str, gate: PiiGatePort) -> MaskedText:
    """Mask with the gate, then phones, e-mails, valid PESEL and ID card numbers.

    A phone-shaped number that continues a digit group or stands before a
    currency or unit is an amount and stays: the claim is about it (#102).

    Idempotent: markers contain no digits or ``@`` and are no personal data, so
    masking twice changes nothing. Run it before a workflow starts and on step
    results. A failing gate is skipped with a log line that never holds the
    text; the patterns still run (ADR-35).

    Args:
        text: Free text that may contain personal data.
        gate: The masking gate from ``build_pii_gate``.

    Returns:
        The masked text and the number of replacements by the gate and patterns.

    Features:
        US-BEZ-04, F-20, ADR-13, ADR-35
    """
    try:
        gated = await gate.mask(text)
    except PiiGateUnavailableError as exc:
        _log.warning("personal-data DLP gate failed (%s); skipped", exc)
        gated = MaskedText(text=text, replaced=0)
    patterned = _mask_patterns(gated.text)
    return MaskedText(text=patterned.text, replaced=gated.replaced + patterned.replaced)
