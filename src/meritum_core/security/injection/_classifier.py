"""Third detector layer: an LLM classifier called in isolation through ``LlmPort``.

Features:
    US-BEZ-01, F-19, ADR-12, ADR-23
"""

from meritum_core.security.injection.constants import CLASSIFIER_TASK
from meritum_core.security.injection.models import InjectionClassification, TextRange
from meritum_core.shared.llm import LlmPort, Prompt


class LlmClassifierGate:
    """Asks a model whether text holds instructions, and where.

    Isolated: the model gets only its classification task, never the pipeline's
    instructions, no tools (``LlmPort`` offers none), and the text only as data.

    Args:
        llm: The model port.

    Features:
        US-BEZ-01, F-19, ADR-12, ADR-23
    """

    def __init__(self, llm: LlmPort) -> None:
        self._llm = llm

    async def screen(self, text: str) -> tuple[TextRange, ...]:
        """Classify ``text`` and locate the quoted instructions in it.

        Args:
            text: User or source text.

        Returns:
            The range of each quoted instruction; the whole text when the model
            flags an injection it does not quote verbatim.
        """
        prompt = Prompt(instructions=CLASSIFIER_TASK, data=(text,))
        answer = (await self._llm.complete(prompt, InjectionClassification)).output
        if not answer.injected:
            return ()
        found = tuple(
            TextRange(start, start + len(quote))
            for quote in answer.instructions
            if quote and (start := text.find(quote)) >= 0
        )
        return found or (TextRange(0, len(text)),)
