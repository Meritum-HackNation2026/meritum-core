"""Text and data mining opt-outs written in a page's own meta tags.

Features:
    US-KOR-01, F-06, ADR-24
"""

from html.parser import HTMLParser
from typing import override

from meritum_core.corpus.fetching.constants import (
    NOAI_DIRECTIVE,
    ROBOTS_META_NAME,
    TDM_META_NAME,
)


class _MetaReader(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.reserved = False

    @override
    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag != "meta":
            return
        found = {k: (v or "").strip().lower() for k, v in attrs}
        name, content = found.get("name", ""), found.get("content", "")
        directives = {d.strip() for d in content.split(",")}
        tdm_reserved = name == TDM_META_NAME and content == "1"
        no_ai = name == ROBOTS_META_NAME and NOAI_DIRECTIVE in directives
        self.reserved = self.reserved or tdm_reserved or no_ai


def meta_reserves_mining(html: str) -> bool:
    """Whether the page's meta tags reserve text and data mining.

    Args:
        html: the page's HTML.

    Returns:
        True for ``tdm-reservation`` set to 1 or a robots ``noai`` directive.

    Features:
        US-KOR-01, F-06, ADR-24
    """
    reader = _MetaReader()
    reader.feed(html)
    return reader.reserved
