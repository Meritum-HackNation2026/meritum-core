"""NotificationRepository contract: every adapter in conftest.py must pass these tests."""

import asyncio
import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

from meritum_core.checks.contracts import Notification
from meritum_core.notifications import NotificationRepository

EXAMPLE = json.loads(
    (Path(__file__).parents[2] / "contracts" / "examples.json").read_text("utf-8")
)["Notification"]
T0 = datetime(2026, 11, 21, 12, tzinfo=UTC)
SESSION = "s_12345678"
USER = "u_12345678"


def note(note_id: str, minute: int = 0, **changes: object) -> Notification:
    at = T0 + timedelta(minutes=minute)
    times = {"created_at": at, "retention_until": at + timedelta(days=30)}
    return Notification.model_validate(
        EXAMPLE | times | {"id": note_id, "session_id": SESSION} | changes
    )


def for_user(note_id: str, minute: int = 0) -> Notification:
    return note(note_id, minute, session_id=None, user_id=USER)


def save(
    run: asyncio.Runner, repo: NotificationRepository, *items: Notification
) -> None:
    for item in items:
        run.run(repo.save(item))


def ids(items: list[Notification]) -> list[str]:
    return [n.id for n in items]


def test_list_for_session_or_user_is_newest_first(
    run: asyncio.Runner, notes: NotificationRepository
) -> None:
    save(
        run, notes, note("n_1", 0), note("n_2", 5), for_user("n_3"), for_user("n_4", 9)
    )
    assert ids(run.run(notes.list_for("session_id", SESSION))) == ["n_2", "n_1"]
    assert ids(run.run(notes.list_for("user_id", USER))) == ["n_4", "n_3"]


def test_saving_the_same_id_again_replaces_it(
    run: asyncio.Runner, notes: NotificationRepository
) -> None:
    save(run, notes, note("n_1"), note("n_1", link="/inne"))
    listed = run.run(notes.list_for("session_id", SESSION))
    assert [n.link for n in listed] == ["/inne"]


def test_mark_read_changes_only_that_notification(
    run: asyncio.Runner, notes: NotificationRepository
) -> None:
    save(run, notes, note("n_1"), note("n_2", 5))
    run.run(notes.mark_read("n_1"))
    run.run(notes.mark_read("n_unknown"))
    listed = run.run(notes.list_for("session_id", SESSION))
    assert [(n.id, n.status) for n in listed] == [("n_2", "unread"), ("n_1", "read")]


def test_delete_for_recipient_removes_only_theirs(
    run: asyncio.Runner, notes: NotificationRepository
) -> None:
    save(run, notes, note("n_1"), note("n_2"), for_user("n_3"))
    assert run.run(notes.delete_for("session_id", SESSION)) == 2
    assert run.run(notes.list_for("session_id", SESSION)) == []
    assert ids(run.run(notes.list_for("user_id", USER))) == ["n_3"]


def test_delete_expired_removes_notifications_past_retention(
    run: asyncio.Runner, notes: NotificationRepository
) -> None:
    save(run, notes, note("n_old", 0), note("n_new", 60 * 24 * 10))
    now = T0 + timedelta(days=30)  # n_old's retention ends exactly now
    assert run.run(notes.delete_expired(now)) == 1
    assert ids(run.run(notes.list_for("session_id", SESSION))) == ["n_new"]
