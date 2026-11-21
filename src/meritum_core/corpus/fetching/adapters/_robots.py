"""robots.txt and its Content-Signal lines, for fetched sources.

Features:
    F-06
"""

from urllib.robotparser import RobotFileParser

from meritum_core.corpus.fetching.constants import CONTENT_SIGNAL_USE, ROBOTS_AGENT


def _applies(agents: set[str]) -> bool:
    return not agents or bool(agents & {"*", ROBOTS_AGENT.lower()})


def _signals(robots_txt: str) -> list[str]:
    # Content-Signal values of groups that apply to us (or of no group at all).
    agents: set[str] = set()
    in_rules, found = False, list[str]()
    for raw in robots_txt.splitlines():
        key, _, value = raw.split("#", 1)[0].partition(":")
        key, value = key.strip().lower(), value.strip()
        if key == "user-agent":
            if in_rules:  # a User-agent line after rules starts a new group
                agents = set()
            agents.add(value.lower())
            in_rules = False
        elif key:
            in_rules = True
            if key == "content-signal" and _applies(agents):
                found.append(value)
    return found


def _signal_allows(value: str) -> bool:
    for pair in value.split(","):
        use, _, answer = pair.partition("=")
        if use.strip().lower() == CONTENT_SIGNAL_USE and answer.strip() == "no":
            return False
    return True


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
    signals_allow = all(map(_signal_allows, _signals(robots_txt)))
    return parser.can_fetch(ROBOTS_AGENT, url) and signals_allow
