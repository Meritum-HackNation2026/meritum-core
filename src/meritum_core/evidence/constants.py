"""Normalization rules of the verbatim citation check: the only differences it forgives.

A model may retype a fragment with other spaces, quotes or dashes; anything else
(letters, case, punctuation, word order) must match the source exactly (ADR-06).

Features:
    US-ZRD-01, F-16, ADR-06
"""

from typing import Final

CITATION_QUOTES: Final = {
    **dict.fromkeys(
        "\u201e\u201c\u201d\u00ab\u00bb\u201f\u2033\u301d\u301e\uff02", '"'
    ),
    **dict.fromkeys("\u201a\u2018\u2019\u2039\u203a\u201b\u2032\uff07`", "'"),
}
"""Typographic quotes (\u201e \u201d \u00ab \u2019 ...) compared as their ASCII form."""

CITATION_DASHES: Final = dict.fromkeys(
    "\u2010\u2011\u2012\u2013\u2014\u2015\u2212\ufe58\ufe63\uff0d", "-"
)
"""Hyphens, dashes and minus signs, all compared as ``-``."""

CITATION_FOLD: Final = str.maketrans(CITATION_QUOTES | CITATION_DASHES)
"""Translation table applying both maps above, one character to one character."""

CITATION_SPACE: Final = " "
"""What every run of whitespace (``str.isspace``: newlines and NBSP included) becomes;
paragraph breaks therefore never stop a fragment from matching."""
