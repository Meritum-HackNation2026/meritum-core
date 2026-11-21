"""Cut detected instructions out of user text and record each cut (ADR-23).

Features:
    US-BEZ-01, F-19, ADR-12, ADR-23
"""

from meritum_core.checks import InjectionEvent
from meritum_core.security.injection.constants import EXCERPT_MAX_LENGTH
from meritum_core.security.injection.models import (
    CleanedInput,
    InjectionScan,
    TextRange,
)


def _merged(scan: InjectionScan) -> list[TextRange]:
    merged: list[TextRange] = []
    for span in scan.spans:  # ordered by start
        if merged and span.start <= merged[-1].end:
            last = merged.pop()
            merged.append(TextRange(last.start, max(last.end, span.end)))
        else:
            merged.append(TextRange(span.start, span.end))
    return merged


def instruction_removed(scan: InjectionScan) -> CleanedInput:
    """Remove every detected instruction from user text; the rest stays as data.

    User input is never rejected: overlapping findings are cut once, the kept
    parts are joined with a space, and each cut becomes an ``InjectionEvent``
    with ``location="input"`` and ``action="instruction_removed"``.

    Args:
        scan: The detector's result for the user's text.

    Returns:
        The text left for analysis and one event per cut.

    Features:
        US-BEZ-01, F-19, ADR-12, ADR-23
    """
    text = scan.text
    cuts = _merged(scan)
    bounds = [0, *(i for cut in cuts for i in cut), len(text)]
    kept = (text[a:b].strip() for a, b in zip(bounds[::2], bounds[1::2], strict=True))
    events = tuple(
        InjectionEvent(
            location="input",
            action="instruction_removed",
            excerpt=text[cut.start : cut.end].strip()[:EXCERPT_MAX_LENGTH],
        )
        for cut in cuts
    )
    return CleanedInput(text=" ".join(part for part in kept if part), events=events)
