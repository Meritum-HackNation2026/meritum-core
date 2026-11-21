"""The issue's restart scenario on a real PostgreSQL: local only, ``-m integration``."""

import asyncio

import pytest

from meritum_core.moderation import StaffAccount
from meritum_core.observability import build_app_repositories
from meritum_core.shared.database import DatabaseProvider, DatabaseSettings


@pytest.mark.integration
def test_issue_scenario_role_survives_a_restart(
    run: asyncio.Runner, app_database_url: str
) -> None:
    settings = DatabaseSettings(
        provider=DatabaseProvider.POSTGRES, url=app_database_url
    )
    before = build_app_repositories(settings).staff
    run.run(
        before.save_account(StaffAccount(email="ola@example.com", role="moderator"))
    )
    after = build_app_repositories(settings).staff
    assert run.run(after.role("ola@example.com")) == "moderator"
