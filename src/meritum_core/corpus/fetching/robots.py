"""Reading robots.txt without fetching anything: the Content-Signal lines.

Features:
    US-KOR-01, F-06
"""

from meritum_core.corpus.fetching.constants import ROBOTS_AGENT


def _applies(agents: set[str]) -> bool:
    return not agents or bool(agents & {"*", ROBOTS_AGENT.lower()})


def content_signals(robots_txt: str) -> list[str]:
    """Content-Signal values of the robots.txt groups that apply to ``ROBOTS_AGENT``.

    A Content-Signal line outside any group applies to every agent.

    Args:
        robots_txt: the file's text.

    Returns:
        Each applicable value as written, e.g. ``search=yes, ai-train=no``.

    Features:
        US-KOR-01, F-06, ADR-24
    """
    agents: set[str] = set()
    in_rules = False
    found: list[str] = []
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
