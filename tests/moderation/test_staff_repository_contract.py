"""StaffRepository contract: every adapter in conftest.py must pass these tests."""

import asyncio

import pytest
from pydantic import ValidationError

from meritum_core.moderation import StaffAccount, StaffRepository

OLA = StaffAccount(email="ola@example.com", role="moderator")
ADAM = StaffAccount(email="adam@example.com", role="analyst")


def test_saved_accounts_are_listed_by_address(
    run: asyncio.Runner, staff: StaffRepository
) -> None:
    run.run(staff.save_account(OLA))
    run.run(staff.save_account(ADAM))
    assert run.run(staff.list_accounts()) == [ADAM, OLA]


def test_role_returns_the_granted_role_and_none_for_unknown_addresses(
    run: asyncio.Runner, staff: StaffRepository
) -> None:
    run.run(staff.save_account(OLA))
    assert run.run(staff.role("ola@example.com")) == "moderator"
    assert run.run(staff.role("nikt@example.com")) is None


def test_saving_an_address_again_changes_its_role(
    run: asyncio.Runner, staff: StaffRepository
) -> None:
    run.run(staff.save_account(OLA))
    admin = StaffAccount(email="ola@example.com", role="admin")
    run.run(staff.save_account(admin))
    assert run.run(staff.list_accounts()) == [admin]


def test_delete_account_takes_the_role_away_and_ignores_unknown_addresses(
    run: asyncio.Runner, staff: StaffRepository
) -> None:
    run.run(staff.save_account(ADAM))
    run.run(staff.delete_account("adam@example.com"))
    run.run(staff.delete_account("nikt@example.com"))
    assert run.run(staff.role("adam@example.com")) is None
    assert run.run(staff.list_accounts()) == []


def test_account_address_is_lower_cased_and_stripped() -> None:
    account = StaffAccount(email="  Ola@Example.COM ", role="moderator")
    assert account.email == "ola@example.com"


@pytest.mark.parametrize("email", ["", "ola", "ola@example", "o la@example.com"])
def test_account_refuses_an_address_without_a_dotted_domain(email: str) -> None:
    with pytest.raises(ValidationError):
        StaffAccount(email=email, role="moderator")
