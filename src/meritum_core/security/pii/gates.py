"""The null masking gate: used when Sensitive Data Protection is not configured.

Features:
    US-BEZ-04, F-20, ADR-13, ADR-35
"""

import logging

from meritum_core.security.pii.models import MaskedText

_log = logging.getLogger(__name__)


class NullPiiGate:
    """Masks nothing and logs that the gate was skipped; never logs the text.

    Features:
        US-BEZ-04, F-20, ADR-13, ADR-35
    """

    async def mask(self, text: str) -> MaskedText:  # ruff: ignore[no-self-use]  # null object: same signature as a real gate
        """Skip the gate.

        Args:
            text: Returned unchanged.

        Returns:
            The text as is, with no replacements.
        """
        _log.info("personal-data DLP gate not configured; skipped")
        return MaskedText(text=text, replaced=0)
