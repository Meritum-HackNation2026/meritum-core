"""In-memory moderation repositories for the tests of the backend and the worker.

Features:
    US-MOD-01, US-MOD-05, US-BEZ-05, F-20, F-25
"""

from collections.abc import Sequence

from meritum_core.checks.contracts import CaseClaim, ModeratorCase
from meritum_core.moderation.models import HighRiskTopic
from meritum_core.moderation.ports import CaseState


class InMemoryModeratorCaseRepository:
    """ModeratorCaseRepository fake that keeps the cases in a dict.

    Features:
        US-MOD-01, US-BEZ-05, F-25
    """

    def __init__(self) -> None:
        self._cases: dict[str, ModeratorCase] = {}
        self._removed: set[str] = set()

    async def save(self, case: ModeratorCase) -> None:
        """Store or update ``case`` under its id, without removed checks.

        Args:
            case: the case to store.
        """
        claims = _without(case.claims, self._removed)
        if claims:
            self._cases[case.id] = case.model_copy(update={"claims": claims})
        else:
            self._cases.pop(case.id, None)

    async def get(self, case_id: str) -> ModeratorCase | None:
        """Read one case.

        Args:
            case_id: the case's id.

        Returns:
            The case or None.
        """
        return self._cases.get(case_id)

    async def find_open(self, claim: str) -> ModeratorCase | None:
        """Find the latest open case grouping ``claim``.

        Args:
            claim: the claim text.

        Returns:
            The case or None.
        """
        found = [
            c
            for c in await self.list_cases("open")
            if claim in {x.claim for x in c.claims}
        ]
        return found[0] if found else None

    async def list_cases(self, state: CaseState | None = None) -> list[ModeratorCase]:
        """List cases, latest first.

        Args:
            state: only cases in this state; all when None.

        Returns:
            The cases.
        """
        found = [c for c in self._cases.values() if state in {None, c.state}]
        return sorted(found, key=lambda c: c.last_seen, reverse=True)

    async def remove_checks(self, check_ids: Sequence[str]) -> None:
        """Drop the checks from every case; empty claims and cases go.

        Args:
            check_ids: the deleted checks.
        """
        gone = set(check_ids)
        self._removed |= gone
        for case in list(self._cases.values()):
            claims = _without(case.claims, gone)
            if not claims:
                del self._cases[case.id]
            elif claims != case.claims:
                self._cases[case.id] = case.model_copy(update={"claims": claims})


def _without(claims: list[CaseClaim], gone: set[str]) -> list[CaseClaim]:
    kept = [(c, [i for i in c.check_ids if i not in gone]) for c in claims]
    return [c.model_copy(update={"check_ids": ids}) for c, ids in kept if ids]


class InMemoryHighRiskTopicRepository:
    """HighRiskTopicRepository fake that keeps the topics in a dict.

    Features:
        US-MOD-05, F-20
    """

    def __init__(self) -> None:
        self._topics: dict[str, HighRiskTopic] = {}

    async def list_topics(self) -> list[HighRiskTopic]:
        """List every topic, sorted by name.

        Returns:
            The topics.
        """
        return [self._topics[name] for name in sorted(self._topics)]

    async def save_topic(self, topic: HighRiskTopic) -> None:
        """Add or replace a topic.

        Args:
            topic: the topic.
        """
        self._topics[topic.name] = topic

    async def delete_topic(self, name: str) -> None:
        """Delete a topic, if present.

        Args:
            name: the topic's name.
        """
        self._topics.pop(name, None)
