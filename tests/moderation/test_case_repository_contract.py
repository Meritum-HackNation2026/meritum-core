"""ModeratorCaseRepository contract: every adapter in conftest.py must pass these tests."""

import asyncio
import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

from meritum_core.checks.contracts import ModeratorCase
from meritum_core.moderation import ModeratorCaseRepository

EXAMPLE = json.loads(
    (Path(__file__).parents[2] / "contracts" / "examples.json").read_text("utf-8")
)["ModeratorCase"]
T0 = datetime(2026, 11, 21, 12, tzinfo=UTC)
CLAIM = "Wczoraj w Gdańsku wyłączono wszystkie bankomaty."


def case(case_id: str, minute: int = 0, **changes: object) -> ModeratorCase:
    at = T0 + timedelta(minutes=minute)
    seen = {"first_seen": at, "last_seen": at}
    return ModeratorCase.model_validate(EXAMPLE | seen | {"id": case_id} | changes)


def claims(*groups: tuple[str, list[str]]) -> list[dict[str, object]]:
    return [{"claim": claim, "check_ids": ids} for claim, ids in groups]


def save(
    run: asyncio.Runner, repo: ModeratorCaseRepository, *items: ModeratorCase
) -> None:
    for item in items:
        run.run(repo.save(item))


def test_save_stores_and_updates_a_case(
    run: asyncio.Runner, cases: ModeratorCaseRepository
) -> None:
    created = case("#S-1")
    save(run, cases, created)
    assert run.run(cases.get("#S-1")) == created
    answered = created.model_copy(update={"state": "answered"})
    save(run, cases, answered)
    assert run.run(cases.get("#S-1")) == answered
    assert run.run(cases.get("#S-404")) is None


def test_find_open_returns_the_open_case_with_that_claim(
    run: asyncio.Runner, cases: ModeratorCaseRepository
) -> None:
    save(run, cases, case("#S-1", state="closed"), case("#S-2", 5))
    found = run.run(cases.find_open(CLAIM))
    assert found is not None
    assert found.id == "#S-2"
    assert run.run(cases.find_open("Inne twierdzenie bez sprawy.")) is None


def test_list_for_panel_is_newest_first_and_filters_by_state(
    run: asyncio.Runner, cases: ModeratorCaseRepository
) -> None:
    save(run, cases, case("#S-1", 0), case("#S-2", 5, state="closed"), case("#S-3", 9))
    assert [c.id for c in run.run(cases.list_cases())] == ["#S-3", "#S-2", "#S-1"]
    assert [c.id for c in run.run(cases.list_cases("open"))] == ["#S-3", "#S-1"]


def test_remove_checks_keeps_the_other_checks_of_a_case(
    run: asyncio.Runner, cases: ModeratorCaseRepository
) -> None:
    grouped = claims((CLAIM, ["c_1", "c_2"]), ("W Gdyni też wyłączono.", ["c_3"]))
    save(run, cases, case("#S-1", claims=grouped))
    run.run(cases.remove_checks(["c_1", "c_3"]))
    stored = run.run(cases.get("#S-1"))
    assert stored is not None
    assert stored.claims == case("#S-1", claims=claims((CLAIM, ["c_2"]))).claims


def test_remove_checks_deletes_a_case_left_without_checks(
    run: asyncio.Runner, cases: ModeratorCaseRepository
) -> None:
    save(run, cases, case("#S-1", claims=claims((CLAIM, ["c_1"]))), case("#S-2"))
    run.run(cases.remove_checks(["c_1"]))
    assert run.run(cases.get("#S-1")) is None
    assert run.run(cases.get("#S-2")) is not None


def test_saving_a_case_read_before_remove_checks_does_not_bring_them_back(
    run: asyncio.Runner, cases: ModeratorCaseRepository
) -> None:
    stale = case("#S-1", claims=claims((CLAIM, ["c_1", "c_2"])))
    save(run, cases, stale)
    run.run(cases.remove_checks(["c_1"]))
    save(run, cases, stale.model_copy(update={"state": "answered"}))
    stored = run.run(cases.get("#S-1"))
    assert stored is not None
    assert stored.state == "answered"
    assert stored.check_ids == ["c_2"]


def test_saving_a_case_left_only_with_removed_checks_stores_nothing(
    run: asyncio.Runner, cases: ModeratorCaseRepository
) -> None:
    stale = case("#S-1", claims=claims((CLAIM, ["c_1"])))
    save(run, cases, stale)
    run.run(cases.remove_checks(["c_1"]))
    save(run, cases, stale)
    assert run.run(cases.get("#S-1")) is None
