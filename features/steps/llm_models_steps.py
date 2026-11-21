"""Steps for the model-choice scenario of features/shared.feature.

Each provider answers from a reply recorded in its own format
(``tests/shared/llm/recordings``) through a mock HTTP transport: no network.
"""

import asyncio
import json
import os
from pathlib import Path

import httpx2
from behave import given, then, when
from behave.runner import Context
from google.oauth2.credentials import Credentials
from pydantic import BaseModel

from meritum_core.checks.contracts import ModelUsage
from meritum_core.shared.llm import LlmSettings, Prompt, build_llm

RECORDINGS = Path(__file__).parents[2] / "tests" / "shared" / "llm" / "recordings"
REGION = {"vertex": "europe-west3", "openrouter": "global"}
RECORDING = {
    "anthropic/claude-haiku-5.5": "openrouter-haiku",
    "gemini-3.5-flash": "vertex",
    "openai/gpt-6.1-terra": "openrouter-terra",
    "stepfun/step-3.7-flash": "openrouter-step",
}
PROMPT = Prompt(instructions="Wypisz twierdzenia.", data=("Sejm przyjął ustawę.",))


class ClaimList(BaseModel):
    """Stand-in for the claim extraction output of `checks`."""

    claims: list[str]


def _restore(name: str, value: str | None) -> None:
    if value is None:
        os.environ.pop(name, None)
    else:
        os.environ[name] = value


@given(
    "MERITUM_LLM_PROVIDER={provider}, MERITUM_LLM_MODEL={model} "
    "i MERITUM_LLM_REASONING={reasoning} ustawione"
)
def given_model_configured(
    context: Context, provider: str, model: str, reasoning: str
) -> None:
    """Configure one of the four models; OpenRouter gets a fake key."""
    values = {
        "MERITUM_LLM_PROVIDER": provider,
        "MERITUM_LLM_MODEL": model,
        "MERITUM_LLM_REASONING": reasoning,
        "MERITUM_LLM_REGION": REGION[provider],
        "MERITUM_LLM_PROJECT": "meritum-test",
        "OPENROUTER_API_KEY": "sk-or-test",  # fake key, no network
    }
    for name, value in values.items():
        context.add_cleanup(_restore, name, os.environ.get(name))
        os.environ[name] = value
    context.provider, context.reasoning = provider, reasoning
    context.recording = RECORDING[model]


@when("workflow woła LlmPort o ustrukturyzowaną odpowiedź")
def when_workflow_calls_the_port(context: Context) -> None:
    """Build from the environment; the provider answers with its recording."""
    body = json.loads((RECORDINGS / f"{context.recording}.json").read_bytes())
    context.sent = []

    def reply(request: httpx2.Request) -> httpx2.Response:
        context.sent.append(request)
        return httpx2.Response(200, json=body)

    client = httpx2.AsyncClient(transport=httpx2.MockTransport(reply), timeout=60)
    token = Credentials(token="recorded")  # ruff: ignore[hardcoded-password-func-arg]  # fake token, no network
    llm = build_llm(LlmSettings(), credentials=token, http_client=client)
    context.result = asyncio.run(llm.complete(PROMPT, ClaimList))


@then("odpowiada wybrany model z wybranym poziomem rozumowania")
def then_the_chosen_model_answers(context: Context) -> None:
    """The request names the model and carries the provider's reasoning field."""
    settings = LlmSettings()
    request = context.sent[0]
    sent = json.loads(request.content)
    if context.provider == "vertex":
        assert request.url.path.endswith(f"/models/{settings.model}:generateContent")
        thinking = sent["generationConfig"]["thinkingConfig"]
        assert thinking["thinking_level"] == context.reasoning.upper()
    else:
        assert sent["model"] == settings.model
        assert sent["reasoning"]["effort"] == context.reasoning
    assert isinstance(context.result.output, ClaimList)


@then("CheckRecord zapisuje dostawcę, model, region i koszt")
def then_check_record_gets_usage(context: Context) -> None:
    """The usage validates as the ModelUsage contract with a positive cost."""
    settings = LlmSettings()
    usage = ModelUsage.model_validate(context.result.usage.model_dump())
    assert (usage.provider, usage.model) == (settings.provider, settings.model)
    assert usage.region.startswith(settings.region)  # OpenRouter adds the upstream
    assert usage.cost_usd > 0
