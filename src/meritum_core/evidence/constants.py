"""Normalization rules of the verbatim citation check and the ClaimReview rating table.

A model may retype a fragment with other spaces, quotes or dashes; anything else
(letters, case, punctuation, word order) must match the source exactly (ADR-06).
Quotes and dashes use the same tables as input normalization in ``checks``.

Features:
    US-ZRD-01, US-KOR-01, F-14, F-16, ADR-06, ADR-34
"""

import re
from collections.abc import Mapping
from types import MappingProxyType
from typing import Final

from meritum_core.checks import DASHES, QUOTES
from meritum_core.checks.contracts import PublisherId, Stance, Verdict

CITATION_FOLD: Final = str.maketrans(QUOTES | DASHES)
"""Typographic quotes compared as ASCII ``"``/``'``; hyphens, dashes and minus
signs compared as ``-``. One character to one character, so positions survive."""

CITATION_SPACE: Final = " "
"""What every run of whitespace (``str.isspace``: newlines and NBSP included) becomes;
paragraph breaks therefore never stop a fragment from matching."""

OUTDATED_VERDICTS: Final[frozenset[Verdict]] = frozenset({"false", "misleading"})
"""Verdicts that take technique ``outdated`` when newer evidence replaced the support
for the claim (US-ZRD-10, ADR-25)."""

RATING_END_PUNCTUATION: Final = " .!?…:;,"
"""Characters a normalized rating loses at its end: ``Fałsz.`` reads as ``Fałsz``
(core#154)."""

RATING_SENTENCE_END: Final = re.compile(r"[.!?…:;]\s")
"""End of a rating's first sentence; ``Fałsz. Szczepionki nie…`` is looked up as
``Fałsz`` when the whole rating is not in the table (core#154)."""

RATING_FOLD: Final = str.maketrans({"ł": "l", "Ł": "l"})
"""Letters with no Unicode decomposition that rating normalization folds by hand;
other diacritics drop with NFKD (ADR-34)."""

_COMMON_RATINGS: Final[Mapping[str, Stance]] = MappingProxyType(
    {
        "falsz": "refutes",
        "false": "refutes",
        "prawda": "supports",
        "true": "supports",
        "czesciowa prawda": "context",
        "manipulacja": "context",
        "misleading": "context",
    }
)
"""Normalized Polish and English ratings shared by the catalogue's fact-checkers."""

CLAIM_REVIEW_STANCES: Final[Mapping[PublisherId, Mapping[str, Stance]]] = (
    MappingProxyType(
        {
            "demagog": _COMMON_RATINGS,
            "fakenews-pl": _COMMON_RATINGS,
            "pravda": _COMMON_RATINGS,
            "afp": MappingProxyType(
                dict(_COMMON_RATINGS)
                | {"wprowadzajace w blad": "context", "brak kontekstu": "context"}
            ),
        }
    )
)
"""Stance of a fact-checker's normalized textualRating, per catalogue ``publisher_id``
(ADR-34: each fact-checker has its own wording). A rating not listed for its publisher
stays context and is never a premise. Verdicts in scenarios A, C and G depend on this
table: change it together with their tests (US-KOR-01, F-14)."""

NO_RETENTION_DIRECTIVES: Final = frozenset({"no-store", "no-cache"})
"""Cache-Control directives after which a ClaimReview rating is not kept past its fetch
(ADR-24); ``no-store`` wins over any ``max-age``."""

MAX_AGE_DIRECTIVE: Final = "max-age"
"""Cache-Control directive giving, in seconds, how long a ClaimReview rating may be kept
(ADR-24)."""
