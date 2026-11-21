"""Normalization rules of the verbatim citation check: the only differences it forgives.

A model may retype a fragment with other spaces, quotes or dashes; anything else
(letters, case, punctuation, word order) must match the source exactly (ADR-06).
Quotes and dashes use the same tables as input normalization in ``checks``.

Features:
    US-ZRD-01, F-16, ADR-06
"""

from typing import Final

from meritum_core.checks import DASHES, QUOTES

CITATION_FOLD: Final = str.maketrans(QUOTES | DASHES)
"""Typographic quotes compared as ASCII ``"``/``'``; hyphens, dashes and minus
signs compared as ``-``. One character to one character, so positions survive."""

CITATION_SPACE: Final = " "
"""What every run of whitespace (``str.isspace``: newlines and NBSP included) becomes;
paragraph breaks therefore never stop a fragment from matching."""
