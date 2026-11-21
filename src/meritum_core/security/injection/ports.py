"""Ports of the injection defence: the composed detector and one detection layer.

Features:
    US-BEZ-01, F-19, ADR-12, ADR-23, ADR-35
"""

from typing import Protocol, runtime_checkable

from meritum_core.security.injection.models import InjectionScan, TextRange


@runtime_checkable
class InjectionGatePort(Protocol):
    """One layer that flags instructions; the classifier gate of ADR-35 implements it.

    Provider adapters (Model Armor, Prompt Guard, Llama Guard) live in the worker
    (worker/032); core keeps the null gate and a fake.

    Features:
        US-BEZ-01, F-19, ADR-12, ADR-23, ADR-35
    """

    async def screen(self, text: str) -> tuple[TextRange, ...]:
        """Return the ranges of ``text`` that hold instructions.

        Args:
            text: User or source text, treated as data.

        Returns:
            Flagged ranges; ``(0, len(text))`` when the provider cannot localise.
        """
        ...


@runtime_checkable
class InjectionDetectorPort(Protocol):
    """The detector every workflow step runs before calling a model.

    Features:
        US-BEZ-01, F-19, ADR-12, ADR-23
    """

    async def scan(self, text: str) -> InjectionScan:
        """Scan ``text`` with every layer.

        Args:
            text: User or source text, treated as data.

        Returns:
            The text with each detected instruction's range and layer.

        Raises:
            ProviderUnavailableError: The classifier's model failed after retries.
        """
        ...
