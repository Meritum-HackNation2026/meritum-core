"""Verbatim citation check: a fragment counts only when it occurs in the source text.

The same check serves the pipeline's citations (US-ZRD-01) and moderators' answers
(US-MOD-07).

Features:
    US-ZRD-01, F-16, ADR-06
"""

from collections.abc import Mapping

from pydantic import ValidationError

from meritum_core.checks.contracts import Citation
from meritum_core.evidence.constants import CITATION_FOLD, CITATION_SPACE
from meritum_core.evidence.models import CitationDraft, SourceDocument


def find_verbatim(fragment: str, source_text: str) -> tuple[int, int] | None:
    """Find ``fragment`` in ``source_text`` up to whitespace, quotes and dashes.

    No paraphrase and no fuzzy matching: letters, case and punctuation must be
    identical (rules in :mod:`meritum_core.evidence.constants`), and the match
    starts and ends on word boundaries, so "zamknięte" never matches inside
    "niezamknięte".

    Args:
        fragment: The quoted fragment, e.g. from a model or a moderator.
        source_text: The full text of the source document.

    Returns:
        ``(start, end)`` such that ``source_text[start:end]`` is the fragment as
        written in the source, or None when it does not occur or is blank.

    Features:
        US-ZRD-01, F-16, ADR-06
    """
    needle, _ = _fold(fragment.strip())
    haystack, positions = _fold(source_text)
    at = haystack.find(needle) if needle else -1
    while at >= 0 and _cuts_a_word(haystack, at, at + len(needle)):
        at = haystack.find(needle, at + 1)
    if at < 0:
        return None
    return positions[at], positions[at + len(needle) - 1] + 1


def verify_citation(
    draft: CitationDraft, sources: Mapping[str, SourceDocument]
) -> Citation | None:
    """Turn a model's citation into a verified one, or drop it.

    Args:
        draft: The citation the model returned.
        sources: The database's documents keyed by source id.

    Returns:
        A Citation with the database's metadata and the fragment exactly as the
        source writes it; None when the source is unknown, the fragment is not
        found verbatim or it breaks the Citation length limits.

    Features:
        US-ZRD-01, F-16, ADR-06
    """
    document = sources.get(draft.source_id)
    if document is None:
        return None
    span = find_verbatim(draft.fragment, document.text)
    if span is None:
        return None
    try:
        return Citation(
            source=document.source,
            fragment=document.text[span[0] : span[1]],
            stance=draft.stance,
            validity=draft.validity,
        )
    except ValidationError:
        return None


def _cuts_a_word(text: str, start: int, end: int) -> bool:
    """Tell whether ``text[start:end]`` begins or ends in the middle of a word.

    Returns:
        True when a letter or digit on either edge continues past the match.
    """
    before = start > 0 and text[start - 1].isalnum() and text[start].isalnum()
    after = end < len(text) and text[end - 1].isalnum() and text[end].isalnum()
    return before or after


def _fold(text: str) -> tuple[str, list[int]]:
    """Apply the normalization rules to ``text``.

    Returns:
        The folded text and, for each of its characters, its index in ``text``.
    """
    chars: list[str] = []
    positions: list[int] = []
    for index, char in enumerate(text):
        if char.isspace() and chars and chars[-1] == CITATION_SPACE:
            continue
        chars.append(
            CITATION_SPACE if char.isspace() else char.translate(CITATION_FOLD)
        )
        positions.append(index)
    return "".join(chars), positions
