"""Ports of the moderation slice: moderator cases and the high-risk topic list.

Features:
    US-MOD-01, US-MOD-05, US-BEZ-05, F-20, F-25
"""

from collections.abc import Sequence
from typing import Literal, Protocol

from meritum_core.checks.contracts import ModeratorCase
from meritum_core.moderation.models import HighRiskTopic

type CaseState = Literal["open", "answered", "closed"]
"""The states of ``ModeratorCase.state``."""


class ModeratorCaseRepository(Protocol):
    """Stores moderator cases (port).

    The worker opens and grows cases, the backend lists them for the panel and
    records decisions. Cases carry no channel user hash, so neither does the
    panel. Every adapter passes the contract test in ``tests/moderation/``.

    Features:
        US-MOD-01, US-MOD-05, US-BEZ-05, F-25
    """

    async def save(self, case: ModeratorCase) -> None:
        """Store a new case or update the stored one with the same ``id``.

        Args:
            case: the case to store.
        """
        ...

    async def get(self, case_id: str) -> ModeratorCase | None:
        """Read one case.

        Args:
            case_id: the case's id, e.g. ``#S-12``.

        Returns:
            The stored case, or None when there is none.
        """
        ...

    async def find_open(self, claim: str) -> ModeratorCase | None:
        """Find the open case that already groups ``claim``, so a repeat joins it.

        Args:
            claim: the claim text, as stored in ``CaseClaim.claim``.

        Returns:
            The open case with the latest ``last_seen``, or None.
        """
        ...

    async def list_cases(self, state: CaseState | None = None) -> list[ModeratorCase]:
        """List cases for the moderator panel, latest ``last_seen`` first.

        Args:
            state: only cases in this state; every case when None.

        Returns:
            The matching cases.
        """
        ...

    async def remove_checks(self, check_ids: Sequence[str]) -> None:
        """Drop deleted checks from every case (US-BEZ-05).

        A claim left without checks goes, and so does a case left without claims.
        ``distinct_askers``, ``first_seen`` and ``last_seen`` stay: they name nobody.

        Args:
            check_ids: the deleted checks.
        """
        ...


class HighRiskTopicRepository(Protocol):
    """Stores the admin's high-risk topic list (port).

    The backend's admin API changes it, the worker's topic step reads it. Every
    adapter passes the contract test in ``tests/moderation/``.

    Features:
        US-MOD-05, F-20
    """

    async def list_topics(self) -> list[HighRiskTopic]:
        """List every topic, sorted by name.

        Returns:
            The topics.
        """
        ...

    async def save_topic(self, topic: HighRiskTopic) -> None:
        """Add a topic or replace the stored one with the same name.

        Args:
            topic: the topic and its keywords.
        """
        ...

    async def delete_topic(self, name: str) -> None:
        """Delete a topic; an unknown name does nothing.

        Args:
            name: the topic's name.
        """
        ...
