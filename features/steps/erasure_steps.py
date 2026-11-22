"""Steps for features/erasure.feature: the in-memory eraser of the factory."""

import asyncio
import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

from behave import given, then, when
from behave.runner import Context

from meritum_core.checks.contracts import CheckRecord, Notification
from meritum_core.observability import build_app_repositories
from meritum_core.shared.database import DatabaseSettings

EXAMPLES = json.loads(
    (Path(__file__).parents[2] / "contracts" / "examples.json").read_text("utf-8")
)
T0 = datetime(2026, 11, 22, 12, tzinfo=UTC)
USER = "u_12345678"


def _note(note_id: str, kind: str, **fields: object) -> Notification:
    times = {"created_at": T0, "retention_until": T0 + timedelta(days=30)}
    to_user = {"session_id": None, "user_id": USER, "check_id": None}
    return Notification.model_validate(
        EXAMPLES["Notification"]
        | times
        | to_user
        | {"id": note_id, "kind": kind}
        | fields
    )


async def _seed(context: Context) -> None:
    app = context.app
    times = {"received_at": T0, "answered_at": T0, "retention_until": T0}
    await app.records.save(
        CheckRecord.model_validate(
            EXAMPLES["CheckRecord"] | times | {"check_id": "c_1", "user_id": USER}
        )
    )
    await app.notifications.save(_note("n_done", "check_done", check_id="c_1"))
    await app.notifications.save(_note("n_case", "case_assigned", case_id="#S-1"))
    await app.notifications.save(
        _note("n_sys", "system", message_code="service_restored")
    )


@given(
    "użytkownik ma powiadomienie check_done o swoim sprawdzeniu, case_assigned o "
    "sprawie #S-1 i system"
)
def step_user_with_notifications(context: Context) -> None:
    """Seed one check and three notifications of the user in the fakes."""
    context.app = build_app_repositories(DatabaseSettings())
    asyncio.run(_seed(context))


@when("eraser usuwa dane tego użytkownika")
def step_erase_user(context: Context) -> None:
    """Erase the user through the factory's eraser."""
    asyncio.run(context.app.eraser.erase("user_id", USER))


@then("zostają tylko powiadomienia case_assigned i system")
def step_only_case_and_system_left(context: Context) -> None:
    """Only the case and system notifications are left; the check is gone."""
    left = asyncio.run(context.app.notifications.list_for("user_id", USER))
    assert sorted(n.kind for n in left) == ["case_assigned", "system"]
    assert asyncio.run(context.app.records.get("c_1")) is None
