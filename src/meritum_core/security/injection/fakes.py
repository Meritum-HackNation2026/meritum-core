"""A configurable classifier gate for tests of the detector and of worker workflows.

Features:
    US-BEZ-01, F-19, ADR-35
"""

from meritum_core.security.injection.models import TextRange


class FakeInjectionGate:
    """Returns preset ranges for every text and records what it screened.

    Attributes:
        screened: Texts passed to ``screen``, in order.

    Args:
        ranges: Ranges returned for every text.

    Features:
        US-BEZ-01, F-19, ADR-35
    """

    screened: list[str]

    def __init__(self, ranges: tuple[TextRange, ...] = ()) -> None:
        self._ranges = ranges
        self.screened = []

    async def screen(self, text: str) -> tuple[TextRange, ...]:
        """Record ``text`` and return the preset ranges.

        Args:
            text: The text to screen.

        Returns:
            The ranges given to the constructor.
        """
        self.screened.append(text)
        return self._ranges
