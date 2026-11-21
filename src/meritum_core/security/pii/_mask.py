"""Masking of personal data: the gate first, then phone, e-mail and PESEL patterns.

Features:
    US-BEZ-04, F-20, ADR-13, ADR-35
"""

import logging
import re

from meritum_core.security.constants import (
    EMAIL_MARKER,
    EMAIL_PATTERN,
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


def _mask_patterns(text: str) -> MaskedText:
    masked = PESEL_PATTERN.sub(_pesel_or_keep, text)
    masked = EMAIL_PATTERN.sub(EMAIL_MARKER, masked)
    masked = PHONE_PATTERN.sub(PHONE_MARKER, masked)
    markers = (PHONE_MARKER, EMAIL_MARKER, PESEL_MARKER)
    # Count added markers only: markers already in the input are not new replacements.
    replaced = sum(masked.count(m) - text.count(m) for m in markers)
    return MaskedText(text=masked, replaced=replaced)


async def mask_personal_data(text: str, gate: PiiGatePort) -> MaskedText:
    """Mask with the gate, then replace phones, e-mails and valid PESEL numbers.

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
