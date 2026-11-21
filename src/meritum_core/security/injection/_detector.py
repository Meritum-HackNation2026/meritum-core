"""The layered detector: runs every layer and widens findings to whole sentences.

Features:
    US-BEZ-01, F-19, ADR-12, ADR-23, ADR-35
"""

from collections.abc import Sequence

from meritum_core.security.injection.constants import SENTENCE_END
from meritum_core.security.injection.models import (
    DetectionLayer,
    InjectionScan,
    InjectionSpan,
    TextRange,
)
from meritum_core.security.injection.ports import InjectionGatePort


def _sentence(text: str, found: TextRange) -> TextRange:
    start, end = found
    # A match may begin at the previous sentence's full stop: start at its first word.
    while start < end and not text[start].isalnum():
        start += 1
    while start > 0 and text[start - 1] not in SENTENCE_END:
        start -= 1
    while start < end and text[start].isspace():
        start += 1
    while end < len(text) and text[end - 1] not in SENTENCE_END:
        end += 1
    while end < len(text) and text[end] in SENTENCE_END - {"\n"}:
        end += 1
    return TextRange(start, end)


def _is_valid(found: TextRange, length: int) -> bool:
    # Ranges come from provider adapters: a trust boundary.
    return 0 <= found.start < found.end <= length


class LayeredInjectionDetector:
    """Runs patterns, the classifier gate and the LLM classifier on the same text.

    Every layer runs, so an instruction one layer misses is still cut out.

    Args:
        layers: Each layer with the name reported for its findings, cheapest first.

    Features:
        US-BEZ-01, F-19, ADR-12, ADR-23, ADR-35
    """

    def __init__(
        self, layers: Sequence[tuple[DetectionLayer, InjectionGatePort]]
    ) -> None:
        self._layers = tuple(layers)

    async def scan(self, text: str) -> InjectionScan:
        """Scan ``text`` with every layer.

        Args:
            text: User or source text.

        Returns:
            Each finding widened to its sentence, with the layer that found it.
        """
        spans: set[InjectionSpan] = set()
        for layer, gate in self._layers:
            for found in await gate.screen(text):
                if _is_valid(found, len(text)):
                    start, end = _sentence(text, found)
                    spans.add(InjectionSpan(start=start, end=end, layer=layer))
        ordered = sorted(spans, key=lambda s: (s.start, s.end, s.layer))
        return InjectionScan(text=text, spans=tuple(ordered))
