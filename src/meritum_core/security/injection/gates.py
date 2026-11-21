"""The null classifier gate: used until a provider is picked (worker/032).

Features:
    US-BEZ-01, F-19, ADR-35
"""

import logging

from meritum_core.security.injection.models import TextRange

_log = logging.getLogger(__name__)


class NullInjectionGate:
    """Flags nothing and logs that the classifier gate was skipped.

    The log line never holds the scanned text.

    Features:
        US-BEZ-01, F-19, ADR-35
    """

    async def screen(self, text: str) -> tuple[TextRange, ...]:  # ruff: ignore[unused-method-argument, no-self-use]  # null object: same signature as a real gate
        """Skip the gate.

        Args:
            text: Ignored.

        Returns:
            No ranges.
        """
        _log.info("injection classifier gate not configured; skipped")
        return ()
