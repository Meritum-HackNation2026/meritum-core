"""SubjectEraser contract: one person's data goes from every app table at once."""

import asyncio
import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

from meritum_core.checks.contracts import CheckRecord, ModeratorCase, Notification
from meritum_core.observability import AppRepositories

EXAMPLES = json.loads(
    (Path(__file__).parents[2] / "contracts" / "examples.json").read_text("utf-8")
)
T0 = datetime(2026, 11, 21, 12, tzinfo=UTC)
SESSION = "s_12345678"
OTHER = "s_87654321"
USER = "u_12345678"
HASH = "b" * 64
CLAIM = "Wczoraj w Gdańsku wyłączono wszystkie bankomaty."


def record(check_id: str, **changes: object) -> CheckRecord:
    times = {"received_at": T0, "answered_at": T0, "retention_until": T0}
    return CheckRecord.model_validate(
        EXAMPLES["CheckRecord"] | times | {"check_id": check_id} | changes
    )


def note(note_id: str, **recipient: object) -> Notification:
    times = {"created_at": T0, "retention_until": T0 + timedelta(days=30)}
    return Notification.model_validate(
        EXAMPLES["Notification"] | times | {"id": note_id} | recipient
    )


def case(case_id: str, *check_ids: str) -> ModeratorCase:
    claims = [{"claim": CLAIM, "check_ids": list(check_ids)}]
    seen = {"first_seen": T0, "last_seen": T0}
    return ModeratorCase.model_validate(
        EXAMPLES["ModeratorCase"] | seen | {"id": case_id, "claims": claims}
    )


def seed(run: asyncio.Runner, app: AppRepositories) -> None:
    items = [
        app.records.save(record("c_s", session_id=SESSION)),
        app.records.save(record("c_u", session_id=OTHER, user_id=USER)),
        app.records.save(
            record("c_d", channel="discord", session_id=HASH, channel_user_hash=HASH)
        ),
        app.records.save(record("c_keep", session_id=OTHER)),
        app.notifications.save(note("n_s", session_id=SESSION)),
        app.notifications.save(note("n_u", session_id=None, user_id=USER)),
        app.notifications.save(note("n_d", session_id=HASH)),
        app.notifications.save(note("n_keep", session_id=OTHER)),
        app.notifications.save(note("n_about_s", session_id=OTHER, check_id="c_s")),
        app.cases.save(case("#S-1", "c_s", "c_keep")),
        app.cases.save(case("#S-2", "c_s")),
    ]
    for item in items:
        run.run(item)


def test_erasing_a_session_removes_its_records_notifications_and_case_checks(
    run: asyncio.Runner, app: AppRepositories
) -> None:
    seed(run, app)
    assert run.run(app.eraser.erase("session_id", SESSION)) == 3
    assert run.run(app.records.get("c_s")) is None
    assert run.run(app.notifications.list_for("session_id", SESSION)) == []
    kept = run.run(app.cases.get("#S-1"))
    assert kept is not None
    assert kept.check_ids == ["c_keep"]
    assert run.run(app.cases.get("#S-2")) is None
    others = run.run(app.notifications.list_for("session_id", OTHER))
    assert [n.id for n in others] == ["n_keep"]  # n_about_s named an erased check


def test_erasing_a_user_or_channel_user_leaves_everyone_else(
    run: asyncio.Runner, app: AppRepositories
) -> None:
    seed(run, app)
    assert run.run(app.eraser.erase("user_id", USER)) == 2
    assert run.run(app.eraser.erase("channel_user_hash", HASH)) == 2
    assert run.run(app.eraser.erase("channel_user_hash", HASH)) == 0
    left = run.run(app.records.list_for("session_id", OTHER))
    assert [r.check_id for r in left] == ["c_keep"]
    notes = run.run(app.notifications.list_for("session_id", OTHER))
    assert sorted(n.id for n in notes) == ["n_about_s", "n_keep"]
    assert run.run(app.notifications.list_for("session_id", HASH)) == []


def test_a_case_saved_from_before_the_erase_stays_without_erased_checks(
    run: asyncio.Runner, app: AppRepositories
) -> None:
    seed(run, app)
    stale = run.run(app.cases.get("#S-1"))
    assert stale is not None
    run.run(app.eraser.erase("session_id", SESSION))
    run.run(app.cases.save(stale))
    stored = run.run(app.cases.get("#S-1"))
    assert stored is not None
    assert stored.check_ids == ["c_keep"]
