"""Fold text for pattern matching while keeping a map back to the original indices.

Features:
    US-BEZ-01, F-19, ADR-12
"""

import unicodedata

from meritum_core.security.injection.constants import DROPPED_CATEGORIES, HOMOGLYPHS


def fold(text: str) -> tuple[str, tuple[int, ...]]:
    """Lower-case ``text``, drop marks and invisible characters, unify look-alikes.

    Args:
        text: The original text.

    Returns:
        The folded text and, per folded character, the index of the original
        character it came from.

    Features:
        US-BEZ-01, F-19, ADR-12
    """
    chars: list[str] = []
    origin: list[int] = []
    for index, char in enumerate(text):
        for part in unicodedata.normalize("NFKD", char):
            if unicodedata.category(part) in DROPPED_CATEGORIES:
                continue
            folded = part.casefold().translate(HOMOGLYPHS)
            chars.append(folded)
            origin.extend([index] * len(folded))
    return "".join(chars), tuple(origin)
