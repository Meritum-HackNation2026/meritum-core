"""CheckRecordRepository contract: every adapter in conftest.py must pass these tests."""

import asyncio
import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

from meritum_core.checks import CheckRecordRepository
from meritum_core.checks.contracts import CheckRecord

EXAMPLE = json.loads(
    (Path(__file__).parents[3] / "contracts" / "examples.json").read_text("utf-8")
)["CheckRecord"]
T0 = datetime(2026, 11, 21, 12, tzinfo=UTC)
SESSION = "s_12345678"
USER = "u_12345678"
HASH = "a" * 64


def record(check_id: str, minute: int = 0, **changes: object) -> CheckRecord:
    at = T0 + timedelta(minutes=minute)
    times = {"received_at": at, "answered_at": at, "retention_until": at}
    return CheckRecord.model_validate(
        EXAMPLE | times | {"check_id": check_id, "session_id": SESSION} | changes
    )


def save(run: asyncio.Runner, repo: CheckRecordRepository, *items: CheckRecord) -> None:
    for item in items:
        run.run(repo.save(item))


def test_get_returns_the_saved_record(
    run: asyncio.Runner, records: CheckRecordRepository
) -> None:
    saved = record("c_1", verdicts=["false", "confirmed"])
    save(run, records, saved)
    assert run.run(records.get("c_1")) == saved
    assert run.run(records.get("c_unknown")) is None


def test_saving_the_same_check_again_replaces_it(
    run: asyncio.Runner, records: CheckRecordRepository
) -> None:
    save(run, records, record("c_1"), record("c_1", cache_hit=True))
    stored = run.run(records.get("c_1"))
    assert stored is not None
    assert stored.cache_hit
    assert len(run.run(records.list_for("session_id", SESSION))) == 1


def test_list_for_session_or_user_is_newest_first(
    run: asyncio.Runner, records: CheckRecordRepository
) -> None:
    save(
        run,
        records,
        record("c_old", 0, user_id=USER),
        record("c_new", 5, user_id=USER),
        record("c_other", 9, session_id="s_87654321"),
    )
    by_session = run.run(records.list_for("session_id", SESSION))
    by_user = run.run(records.list_for("user_id", USER))
    assert [r.check_id for r in by_session] == ["c_new", "c_old"]
    assert [r.check_id for r in by_user] == ["c_new", "c_old"]


def test_delete_subject_removes_only_that_subjects_records(
    run: asyncio.Runner, records: CheckRecordRepository
) -> None:
    save(
        run,
        records,
        record("c_s"),
        record("c_u", session_id="s_87654321", user_id=USER),
        record("c_d", channel="discord", session_id=HASH, channel_user_hash=HASH),
        record("c_keep", session_id="s_87654321"),
    )
    assert run.run(records.delete_subject("session_id", SESSION)) == ["c_s"]
    assert run.run(records.delete_subject("user_id", USER)) == ["c_u"]
    assert run.run(records.delete_subject("channel_user_hash", HASH)) == ["c_d"]
    assert run.run(records.delete_subject("session_id", SESSION)) == []
    left = run.run(records.list_for("session_id", "s_87654321"))
    assert [r.check_id for r in left] == ["c_keep"]


def test_expired_selects_records_past_retention_oldest_first(
    run: asyncio.Runner, records: CheckRecordRepository
) -> None:
    save(run, records, record("c_2", 2), record("c_1", 1), record("c_9", 9))
    now = T0 + timedelta(minutes=5)
    assert run.run(records.expired(now, limit=10)) == ["c_1", "c_2"]
    assert run.run(records.expired(now, limit=1)) == ["c_1"]


def test_delete_removes_the_given_checks_and_ignores_unknown_ids(
    run: asyncio.Runner, records: CheckRecordRepository
) -> None:
    save(run, records, record("c_1"), record("c_2"))
    run.run(records.delete(["c_1", "c_unknown"]))
    assert run.run(records.get("c_1")) is None
    assert run.run(records.get("c_2")) is not None
