"""Steps for features/shared.feature: the LLM port picked by MERITUM_LLM_* settings.

No step reaches the network: the stub reads a fixture file and the Vertex adapter
answers from a recorded reply through a mock HTTP transport.
"""

import asyncio
import json
import os
import shutil
import socket
import tempfile
from pathlib import Path

import httpx2
from behave import given, then, when
from behave.runner import Context
from google.oauth2.credentials import Credentials
from pydantic import BaseModel

from meritum_core.shared.llm import LlmSettings, Prompt, build_llm

ANSWER = {"claims": ["Sejm przyjął ustawę."]}
REPLY = {
    "candidates": [
        {
            "content": {
                "role": "model",
                "parts": [{"functionCall": {"name": "final_result", "args": ANSWER}}],
            },
            "finishReason": "STOP",
        }
    ],
    "usageMetadata": {"promptTokenCount": 42, "candidatesTokenCount": 7},
}
PROMPT = Prompt(instructions="Wypisz twierdzenia.", data=("Sejm przyjął ustawę.",))


class ClaimList(BaseModel):
    """Stand-in for the claim extraction output of `checks`."""

    claims: list[str]


def _set_env(context: Context, values: dict[str, str]) -> None:
    """Set environment variables for one scenario and restore them after it."""
    for name, value in values.items():
        context.add_cleanup(_restore, name, os.environ.get(name))
        os.environ[name] = value


def _restore(name: str, value: str | None) -> None:
    if value is None:
        os.environ.pop(name, None)
    else:
        os.environ[name] = value


def _no_network(*_args: object, **_kwargs: object) -> object:
    msg = "the stub must not open a network connection"
    raise AssertionError(msg)


@given("MERITUM_LLM_PROVIDER=stub i brak kluczy dostawcy")
def given_stub_without_keys(context: Context) -> None:
    """Stub provider with a fixture file; no Google variables at all."""
    folder = Path(tempfile.mkdtemp())
    context.add_cleanup(shutil.rmtree, folder)
    fixtures = folder / "llm-stub.json"
    fixtures.write_text(json.dumps({"ClaimList": ANSWER}), encoding="utf-8")
    _set_env(
        context,
        {"MERITUM_LLM_PROVIDER": "stub", "MERITUM_LLM_STUB_FIXTURES": str(fixtures)},
    )
    for name in ("GOOGLE_API_KEY", "GOOGLE_APPLICATION_CREDENTIALS"):
        context.add_cleanup(_restore, name, os.environ.pop(name, None))


@when("workflow prosi model o strukturalną odpowiedź typu ClaimList")
def when_workflow_asks_for_claim_list(context: Context) -> None:
    """Ask through the port, with DNS lookups and connections disabled."""
    llm = build_llm(LlmSettings())
    real_lookup, real_connect = socket.getaddrinfo, socket.socket.connect
    socket.getaddrinfo = _no_network  # ty: ignore[invalid-assignment]  # this call only
    socket.socket.connect = _no_network  # ty: ignore[invalid-assignment]  # this call only
    try:
        context.result = asyncio.run(llm.complete(PROMPT, ClaimList))
    finally:
        socket.getaddrinfo, socket.socket.connect = real_lookup, real_connect


@then("dostaje poprawny obiekt ClaimList z danych stubu, bez wywołań sieci")
def then_gets_claim_list_from_stub(context: Context) -> None:
    """The answer is the fixture, validated as ClaimList."""
    output = context.result.output
    assert isinstance(output, ClaimList)
    assert output.claims == ANSWER["claims"]


@given(
    "MERITUM_LLM_PROVIDER=vertex, region UE i przypięta wersja modelu w konfiguracji"
)
def given_vertex_configured(context: Context) -> None:
    """Vertex in an EU region with a pinned model version."""
    _set_env(
        context,
        {
            "MERITUM_LLM_PROVIDER": "vertex",
            "MERITUM_LLM_REGION": "europe-west4",
            "MERITUM_LLM_MODEL": "gemini-2.5-flash-001",
            "MERITUM_LLM_PROJECT": "meritum-test",
        },
    )


@when("fabryka buduje adapter")
def when_factory_builds_adapter(context: Context) -> None:
    """Build from the environment with a recorded reply as the HTTP transport."""
    context.sent = []

    def reply(request: httpx2.Request) -> httpx2.Response:
        context.sent.append(request)
        return httpx2.Response(200, json=REPLY)

    client = httpx2.AsyncClient(transport=httpx2.MockTransport(reply), timeout=60)
    token = Credentials(token="recorded")  # ruff: ignore[hardcoded-password-func-arg]  # fake token, no network
    llm = build_llm(LlmSettings(), credentials=token, http_client=client)
    context.result = asyncio.run(llm.complete(PROMPT, ClaimList))


@then("adapter używa temperatury 0 i przypiętej wersji modelu")
def then_uses_temperature_zero_and_pinned_model(context: Context) -> None:
    """The request carries temperature 0 and targets the configured model."""
    request = context.sent[0]
    assert json.loads(request.content)["generationConfig"]["temperature"] == 0
    assert request.url.path.endswith("/models/gemini-2.5-flash-001:generateContent")


@then("zwraca dostawcę, model, region i zużycie tokenów do zapisu w ModelUsage")
def then_returns_usage(context: Context) -> None:
    """Usage names the provider, pinned model, EU region and token counts."""
    usage = context.result.usage
    assert (usage.provider, usage.model, usage.region) == (
        "vertex",
        "gemini-2.5-flash-001",
        "europe-west4",
    )
    assert (usage.input_tokens, usage.output_tokens) == (42, 7)
