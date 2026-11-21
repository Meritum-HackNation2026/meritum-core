"""Steps for features/moderation.feature: staff roles behind StaffRepository.

The database is one in-memory repository that outlives the API, as the
PostgreSQL schema does in production; the restart on a real PostgreSQL is
``tests/moderation/test_staff_repository_integration.py`` (local only).
"""

import asyncio

from behave import given, then, when
from behave.runner import Context

from meritum_core.checks.contracts import StaffRole
from meritum_core.moderation import StaffAccount, StaffRepository
from meritum_core.moderation.fakes import InMemoryStaffRepository


def _grant(context: Context, email: str, role: StaffRole) -> None:
    context.database = InMemoryStaffRepository()
    context.api_staff = context.database
    context.email = email
    account = StaffAccount(email=email, role=role)
    asyncio.run(context.api_staff.save_account(account))


@given('administrator nadał adresowi "{email}" rolę "{role}"')
def given_admin_granted_role(context: Context, email: str, role: StaffRole) -> None:
    """The admin grants a role through the API's repository."""
    _grant(context, email, role)


@given('adres "{email}" z rolą "{role}"')
def given_address_with_role(context: Context, email: str, role: StaffRole) -> None:
    """An address that already has a role."""
    _grant(context, email, role)


@when("API startuje ponownie z tą samą bazą")
def when_api_restarts(context: Context) -> None:
    """The new API process reaches the same store; nothing of the old one stays."""
    staff: StaffRepository = context.database
    context.api_staff = staff


@when("administrator odbiera mu rolę")
def when_admin_revokes_role(context: Context) -> None:
    """The admin takes the role away."""
    asyncio.run(context.api_staff.delete_account(context.email))


@then('repozytorium kont personelu nadal zwraca dla tego adresu rolę "{role}"')
def then_role_is_still_there(context: Context, role: str) -> None:
    """The role is read back after the restart."""
    assert asyncio.run(context.api_staff.role(context.email)) == role


@then("repozytorium nie zwraca dla tego adresu żadnej roli")
def then_no_role(context: Context) -> None:
    """The address has no role any more."""
    assert asyncio.run(context.api_staff.role(context.email)) is None
