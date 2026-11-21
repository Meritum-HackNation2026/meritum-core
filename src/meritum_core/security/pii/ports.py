"""The masking gate port: text in, text with personal data replaced out.

Features:
    US-BEZ-04, F-20, ADR-13, ADR-35
"""

from typing import Protocol, runtime_checkable

from meritum_core.security.pii.models import MaskedText


@runtime_checkable
class PiiGatePort(Protocol):
    """Masks personal data the patterns do not know, before any model sees it.

    Features:
        US-BEZ-04, F-20, ADR-13, ADR-35
    """

    async def mask(self, text: str) -> MaskedText:
        """Replace personal data in ``text`` with the markers of ``constants.py``.

        Args:
            text: Free text that may contain personal data.

        Returns:
            The masked text and how many items the gate replaced.

        Raises:
            PiiGateUnavailableError: The provider failed; the caller skips the gate.
        """
        ...
