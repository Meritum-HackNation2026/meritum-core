"""Third detector layer: an LLM classifier called in isolation through ``LlmPort``.

Features:
    US-BEZ-01, F-19, ADR-12, ADR-23
"""

import re

from meritum_core.security.injection._folding import fold
from meritum_core.security.injection.constants import (
    CLASSIFIER_TASK,
    MIN_QUOTE_WORDS,
    QUOTE_GAP,
)
from meritum_core.security.injection.models import InjectionClassification, TextRange
from meritum_core.shared.llm import LlmPort, Prompt


def _occurrences(text: str, quote: str) -> list[TextRange]:
    # Match on folded text, word by word, so case, quote marks and spacing may differ.
    words = re.findall(r"\w+", fold(quote)[0])
    if len(words) < MIN_QUOTE_WORDS:
        return []
    folded, origin = fold(text)
    pattern = re.compile(rf"\b{QUOTE_GAP.join(map(re.escape, words))}\b")
    return [
        TextRange(origin[m.start()], origin[m.end() - 1] + 1)
        for m in pattern.finditer(folded)
    ]


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
            model flags an injection and any quote is too short or missing.
        """
        prompt = Prompt(instructions=CLASSIFIER_TASK, data=(text,))
        answer = (await self._llm.complete(prompt, InjectionClassification)).output
        if not answer.injected:
            return ()
        found = [_occurrences(text, quote) for quote in answer.instructions]
        if not found or not all(found):
            # An instruction the model did not quote verbatim cannot be located.
            return (TextRange(0, len(text)),)
        return tuple(r for ranges in found for r in ranges)
