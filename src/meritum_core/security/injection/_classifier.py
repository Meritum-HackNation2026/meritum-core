"""Third detector layer: an LLM classifier called in isolation through ``LlmPort``.

Features:
    US-BEZ-01, F-19, ADR-12, ADR-23
"""

from meritum_core.security.injection.constants import CLASSIFIER_TASK
from meritum_core.security.injection.models import InjectionClassification, TextRange
from meritum_core.shared.llm import LlmPort, Prompt


def _occurrences(text: str, quote: str) -> list[TextRange]:
    ranges: list[TextRange] = []
    start = text.find(quote)
    while start >= 0:
        ranges.append(TextRange(start, start + len(quote)))
        start = text.find(quote, start + 1)
    return ranges


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
            Every occurrence of each quoted instruction; the whole text when the
            model flags an injection and any quote is missing from the text.
        """
        prompt = Prompt(instructions=CLASSIFIER_TASK, data=(text,))
        answer = (await self._llm.complete(prompt, InjectionClassification)).output
        if not answer.injected:
            return ()
        quotes = [quote for quote in answer.instructions if quote.strip()]
        found = [_occurrences(text, quote) for quote in quotes]
        if not quotes or not all(found):
            # An instruction the model did not quote verbatim cannot be located.
            return (TextRange(0, len(text)),)
        return tuple(r for ranges in found for r in ranges)
