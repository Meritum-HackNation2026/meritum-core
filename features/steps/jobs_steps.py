"""Steps for features/jobs.feature: the backend's side of the job contract."""

import asyncio
import hashlib
import hmac
from datetime import UTC, datetime

from behave import given, then, when
from behave.runner import Context
from pydantic import ValidationError

from meritum_core.checks import AnalysisStatus, CheckRequest, CheckResult
from meritum_core.jobs.constants import PROGRESS_KEY
from meritum_core.jobs.contracts import CHECK, WORKFLOWS, CheckInput
from meritum_core.jobs.fakes import InMemoryJobQueue

_SALT = b"behave-salt"


@given("CheckRequest z kanału discord z identyfikatorem użytkownika kanału")
def given_discord_request(context: Context) -> None:
    """A Discord request plus the raw user id the bot saw."""
    context.request = CheckRequest(channel="discord", text="Polska przyjęła euro.")
    context.raw_user_id = "123456789012345678"


@when('backend buduje wejście workflowu "{name}"')
def when_backend_builds_input(context: Context, name: str) -> None:
    """Hash the user id like the backend does and validate the input by spec."""
    spec = next(s for s in WORKFLOWS if s.name == name)
    user_hash = hmac.new(
        _SALT, context.raw_user_id.encode(), hashlib.sha256
    ).hexdigest()
    context.input = spec.input.model_validate(
        {
            "request": context.request.model_dump(mode="json"),
            "session_id": user_hash,
            "channel_user_hash": user_hash,
            "received_at": datetime.now(UTC).isoformat(),
        }
    )
    context.user_hash = user_hash


@then(
    "wejście ma zamaskowany tekst, session_id i channel_user_hash, "
    "a surowego identyfikatora nie ma w żadnym polu"
)
def then_input_has_no_raw_id(context: Context) -> None:
    """The input keeps the text and the hash, never the raw id."""
    built = context.input
    assert isinstance(built, CheckInput)
    assert built.request.text == context.request.text
    assert built.session_id == built.channel_user_hash == context.user_hash
    assert context.raw_user_id not in built.model_dump_json()
    for field in ("session_id", "user_id"):
        leaked = built.model_dump(mode="json") | {field: context.raw_user_id}
        rejected = False
        try:
            CheckInput.model_validate(leaked)
        except ValidationError:
            rejected = True
        assert rejected, f"the contract accepted a raw channel user id in {field}"


def _status(check_id: str, step: str, *, result: CheckResult | None) -> AnalysisStatus:
    steps = [{"code": "receive", "status": step}]
    return AnalysisStatus.model_validate(
        {
            "check_id": check_id,
            "steps": steps,
            "result": result,
        }
    )


@given('workflow "check" publikuje trzy kolejne AnalysisStatus')
def given_three_statuses(context: Context) -> None:
    """Enqueue a check on the fake and publish three statuses to its stream."""
    queue = InMemoryJobQueue()
    request = CheckRequest(channel="web", text="Polska przyjęła euro.")
    payload = CheckInput(
        request=request, session_id="session-1", received_at=datetime.now(UTC)
    )
    workflow_id = asyncio.run(queue.enqueue(CHECK, payload))
    result = CheckResult(
        check_id="c1",
        status="needs_clarification",
        message="Doprecyzuj pytanie.",
        corpus_version="v1",
    )
    context.published = [
        _status("c1", "pending", result=None),
        _status("c1", "active", result=None),
        _status("c1", "done", result=result),
    ]
    for status in context.published:
        queue.publish(workflow_id, PROGRESS_KEY, status)
    context.queue, context.workflow_id = queue, workflow_id


@when("backend czyta strumień przez JobQueue")
def when_backend_reads_stream(context: Context) -> None:
    """Read the whole progress stream through the port."""

    async def read() -> list[AnalysisStatus]:
        stream = context.queue.stream(context.workflow_id, PROGRESS_KEY, AnalysisStatus)
        return [status async for status in stream]

    context.read = asyncio.run(read())


@then("dostaje je w tej kolejności, a ostatni ma pole result")
def then_statuses_in_order(context: Context) -> None:
    """Order is kept and only the last status carries the result."""
    assert context.read == context.published
    assert context.read[-1].result is not None
    assert all(status.result is None for status in context.read[:-1])
