"""robots.txt and its Content-Signal lines, for fetched sources.

Features:
    F-06
"""

from urllib.robotparser import RobotFileParser

from meritum_core.corpus.fetching.constants import CONTENT_SIGNAL_USE, ROBOTS_AGENT
from meritum_core.corpus.fetching.robots import content_signals, signal_denies


def robots_allow(robots_txt: str, url: str) -> bool:
    """Whether robots.txt lets ``ROBOTS_AGENT`` fetch ``url`` as an AI input.

    Args:
        robots_txt: the file's text.
        url: the page to fetch.

    Returns:
        False when a Disallow rule matches or Content-Signal says ``ai-input=no``.

    Features:
        F-06
    """
    parser = RobotFileParser()
    parser.parse(robots_txt.splitlines())
    signals_allow = not any(
        signal_denies(s, {CONTENT_SIGNAL_USE}) for s in content_signals(robots_txt)
    )
    return parser.can_fetch(ROBOTS_AGENT, url) and signals_allow
