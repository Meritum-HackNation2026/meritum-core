"""First detector layer: the PL/EN patterns of ``constants.py`` on folded text.

Features:
    US-BEZ-01, F-19, ADR-12, ADR-23
"""

from meritum_core.security.injection._folding import fold
from meritum_core.security.injection.constants import INJECTION_PATTERNS
from meritum_core.security.injection.models import TextRange


class PatternGate:
    """Flags text that matches a known PL or EN injection pattern.

    Features:
        US-BEZ-01, F-19, ADR-12, ADR-23
    """

    async def screen(self, text: str) -> tuple[TextRange, ...]:  # ruff: ignore[no-self-use]  # implements InjectionGatePort
        """Return the original ranges of every pattern match.

        Args:
            text: User or source text.

        Returns:
            One range per match, in the original text's indices.
        """
        folded, origin = fold(text)
        return tuple(
            TextRange(origin[m.start()], origin[m.end() - 1] + 1)
            for pattern in INJECTION_PATTERNS
            for m in pattern.finditer(folded)
            if m.end() > m.start()
        )
