"""Constants of the checks slice.

Features: US-WTY-03, F-05, ADR-19
"""

import re
from typing import Final

NORMALIZATION_VERSION: Final = 1
"""Version of the normalization rules; part of every result-cache key.

Raise it whenever the rules change, so entries keyed by the old rules are never hit.
"""

TRACKING_PARAMS: Final = frozenset(
    {
        "fbclid",
        "gclid",
        "igshid",
        "mc_cid",
        "mc_eid",
        "ref",
        "ref_src",
        "s",
        "si",
    }
)
"""Query parameters that only track the sharer and never identify the post."""

TRACKING_PREFIXES: Final = ("utm_",)
"""Prefixes of tracking query parameters (``utm_source``, ``utm_medium``...)."""

QUOTES: Final = {
    **dict.fromkeys(
        "\u201e\u201c\u201d\u00ab\u00bb\u201f\u2033\u301d\u301e\uff02", '"'
    ),
    **dict.fromkeys("\u201a\u2018\u2019\u2039\u203a\u201b\u2032\uff07`", "'"),
}
"""Typographic quotes (\u201e \u201d \u00ab \u2019 ...) and their ASCII form."""

DASHES: Final = dict.fromkeys(
    "\u2010\u2011\u2012\u2013\u2014\u2015\u2212\ufe58\ufe63\uff0d", "-"
)
"""Hyphens, dashes and minus signs, all written as ``-``."""

URL_PATTERN: Final = re.compile(r"https?://\S+", re.IGNORECASE)
"""An http(s) URL inside pasted text; it runs until the next whitespace."""

WHITESPACE: Final = re.compile(r"\s+")
"""Any run of Unicode whitespace, non-breaking spaces and newlines included."""

URL_TRAILING_PUNCTUATION: Final = ".,;:!?)\"'"
"""Characters that end a sentence after a pasted URL and are not part of it."""

URL_SCHEMES: Final = frozenset({"http", "https"})
"""Schemes a post URL may have; anything else is dropped from the context."""
