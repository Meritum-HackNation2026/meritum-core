"""PostgresSubjectEraser is all or nothing: local only, ``uv run pytest -m integration``."""

import asyncio
import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

import psycopg
import pytest

from meritum_core.checks.contracts import CheckRecord, ModeratorCase, Notification
from meritum_core.observability import build_app_repositories
from meritum_core.shared.database import DatabaseProvider, DatabaseSettings

EXAMPLES = json.loads(
    (Path(__file__).parents[2] / "contracts" / "examples.json").read_text("utf-8")
)
T0 = datetime(2026, 11, 21, 12, tzinfo=UTC)
SESSION = "s_12345678"
FAIL_ON_NOTIFICATION_DELETE = """
CREATE FUNCTION refuse() RETURNS trigger LANGUAGE plpgsql AS
$$ BEGIN RAISE EXCEPTION 'notifications are locked'; END $$;
CREATE TRIGGER refuse BEFORE DELETE ON notifications
    FOR EACH ROW EXECUTE FUNCTION refuse();
"""


@pytest.mark.integration
def test_a_failure_halfway_leaves_every_table_as_it_was(app_database_url: str) -> None:
    app = build_app_repositories(
        DatabaseSettings(provider=DatabaseProvider.POSTGRES, url=app_database_url)
    )
    record = CheckRecord.model_validate(
        EXAMPLES["CheckRecord"]
        | {"check_id": "c_s", "session_id": SESSION}
        | dict.fromkeys(("received_at", "answered_at", "retention_until"), T0)
    )
    case = ModeratorCase.model_validate(
        EXAMPLES["ModeratorCase"]
        | {"id": "#S-1", "first_seen": T0, "last_seen": T0}
        | {"claims": [{"claim": "Wczoraj wyłączono bankomaty.", "check_ids": ["c_s"]}]}
    )
    note = Notification.model_validate(
        EXAMPLES["Notification"]
        | {"id": "n_s", "session_id": SESSION, "created_at": T0}
        | {"retention_until": T0 + timedelta(days=30)}
    )
    with asyncio.Runner() as run:
        run.run(app.records.save(record))
        run.run(app.cases.save(case))
        run.run(app.notifications.save(note))
        with psycopg.connect(app_database_url, autocommit=True) as conn:
            conn.execute(FAIL_ON_NOTIFICATION_DELETE)
        with pytest.raises(psycopg.errors.RaiseException):
            run.run(app.eraser.erase("session_id", SESSION))
        assert run.run(app.records.get("c_s")) == record
        assert run.run(app.cases.get("#S-1")) == case
        assert run.run(app.notifications.list_for("session_id", SESSION)) == [note]
