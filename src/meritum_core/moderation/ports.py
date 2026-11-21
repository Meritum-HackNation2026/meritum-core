"""Ports of the moderation slice: moderator cases, high-risk topics and staff roles.

Features:
    US-MOD-01, US-MOD-05, US-BEZ-05, F-20, F-25
"""

from collections.abc import Sequence
from typing import Literal, Protocol

from meritum_core.checks.contracts import ModeratorCase, StaffRole
from meritum_core.moderation.models import HighRiskTopic, StaffAccount

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

        Checks dropped earlier by ``remove_checks`` are left out, so a case read
        before a deletion cannot bring them back; a case left without claims is
        not stored (and a stored one goes).

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


class StaffRepository(Protocol):
    """Stores the panel roles administrators grant (port).

    The backend's admin API changes it and its staff gate reads it. Addresses
    are lower-cased (``StaffAccount.email``); callers pass them lower-cased to
    ``role`` and ``delete_account``. Every adapter passes the contract test in
    ``tests/moderation/``.

    Features:
        US-MOD-05, F-25
    """

    async def list_accounts(self) -> list[StaffAccount]:
        """List every account, sorted by address.

        Returns:
            The accounts.
        """
        ...

    async def save_account(self, account: StaffAccount) -> None:
        """Grant a role, replacing the address's previous one.

        Args:
            account: the address and its role.
        """
        ...

    async def delete_account(self, email: str) -> None:
        """Take the role away; an unknown address does nothing.

        Args:
            email: the lower-cased address.
        """
        ...

    async def role(self, email: str) -> StaffRole | None:
        """Read the role granted to an address.

        Args:
            email: the lower-cased address.

        Returns:
            The role, or None when the address has no account.
        """
        ...
