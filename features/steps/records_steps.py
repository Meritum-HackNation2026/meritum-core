"""Steps for the repository scenarios in features/checks.feature.

The worker and the backend share one in-memory repository, as they share one
database schema in production; nothing here talks to PostgreSQL.
"""

import asyncio
import json
from datetime import timedelta
from pathlib import Path

from behave import given, then, when
from behave.runner import Context

from meritum_core.checks import CheckRecordRepository
from meritum_core.checks.contracts import CheckRecord, ModeratorCase
from meritum_core.checks.fakes import InMemoryCheckRecordRepository
from meritum_core.moderation.fakes import InMemoryModeratorCaseRepository

_EXAMPLES = json.loads(
    (Path(__file__).parents[2] / "contracts" / "examples.json").read_text("utf-8")
)
_OTHER_CHECK = "c_other"


def _record(check_id: str, session_id: str) -> CheckRecord:
    return CheckRecord.model_validate(
        _EXAMPLES["CheckRecord"] | {"check_id": check_id, "session_id": session_id}
    )


@given("CheckRecord ze stanem done i dwoma werdyktami")
def given_done_record(context: Context) -> None:
    """A finished check with two verdicts, as the worker stores it."""
    record = _record("c_02", "s_7f3a9c21")
    context.record = record.model_copy(update={"verdicts": ["false", "confirmed"]})


@when("worker zapisuje go przez repozytorium, a backend czyta po check_id")
def when_worker_saves_and_backend_reads(context: Context) -> None:
    """Save and read through the port."""
    repository: CheckRecordRepository = InMemoryCheckRecordRepository()
    asyncio.run(repository.save(context.record))
    context.read = asyncio.run(repository.get(context.record.check_id))


@then("backend dostaje ten sam CheckRecord, z question_masked i bez surowego tekstu")
def then_backend_gets_same_record(context: Context) -> None:
    """Same record, masked question, no raw text field."""
    assert context.read == context.record
    stored = context.read.model_dump()
    assert stored["question_masked"] == context.record.question_masked
    assert "text" not in stored


@given('trzy zapisy z session_id "{session_id}" i jedna sprawa z ich twierdzeniami')
def given_session_records_and_case(context: Context, session_id: str) -> None:
    """Three records of one session and a case that also groups another check."""
    context.session_id = session_id
    context.ids = [f"c_{i}" for i in range(3)]
    context.records = InMemoryCheckRecordRepository()
    context.cases = InMemoryModeratorCaseRepository()
    for check_id in context.ids:
        asyncio.run(context.records.save(_record(check_id, session_id)))
    asyncio.run(context.records.save(_record(_OTHER_CHECK, "s_87654321")))
    claims = [
        {"claim": "Wczoraj w Gdańsku wyłączono bankomaty.", "check_ids": context.ids},
        {"claim": "W Gdyni też wyłączono bankomaty.", "check_ids": [_OTHER_CHECK]},
    ]
    case = ModeratorCase.model_validate(_EXAMPLES["ModeratorCase"] | {"claims": claims})
    asyncio.run(context.cases.save(case))
    context.case_id = case.id


@when("repozytorium usuwa dane tej sesji")
def when_repository_deletes_session(context: Context) -> None:
    """Delete the session's records, then drop their ids from cases."""
    deleted = asyncio.run(
        context.records.delete_subject("session_id", context.session_id)
    )
    asyncio.run(context.cases.remove_checks(deleted))
    context.deleted = deleted


@then("zapisy znikają, a sprawa traci tylko ich check_ids")
def then_records_gone_case_keeps_others(context: Context) -> None:
    """The session has no records left; the case keeps the other check only."""
    assert sorted(context.deleted) == context.ids
    left = asyncio.run(context.records.list_for("session_id", context.session_id))
    assert left == []
    assert asyncio.run(context.records.get(_OTHER_CHECK)) is not None
    case = asyncio.run(context.cases.get(context.case_id))
    assert case is not None
    assert case.check_ids == [_OTHER_CHECK]


@when("analityk pobiera sprawdzenia z okresu obejmującego ten zapis")
def when_analyst_lists_records(context: Context) -> None:
    """Read the export window through the repository port."""
    repository: CheckRecordRepository = InMemoryCheckRecordRepository()
    record = context.record
    assert isinstance(record, CheckRecord)
    asyncio.run(repository.save(record))
    context.exported_records = asyncio.run(
        repository.list_between(
            record.received_at, record.received_at + timedelta(days=1), 10
        )
    )


@then("lista do eksportu zawiera zapisane sprawdzenie")
def then_export_list_contains_record(context: Context) -> None:
    """The saved check is available through the export query."""
    assert context.exported_records == [context.record]
