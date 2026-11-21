"""Port contract of the OpenRouter adapter, on a recorded reply: no network."""

import asyncio
import json
from collections.abc import Callable

import httpx2
import pytest
from pydantic import BaseModel, ValidationError

from meritum_core.shared.llm import (
    LlmPort,
    LlmSettings,
    Prompt,
    ProviderUnavailableError,
)

PROMPT = Prompt(instructions="Wypisz twierdzenia.", data=("Sejm przyjął ustawę.",))
KEY = "sk-or-test-not-a-real-key"  # fake key, no network

type Sent = list[httpx2.Request]
type RecordedFactory = Callable[[LlmSettings, str, int], tuple[LlmPort, Sent]]


@pytest.fixture
def openrouter_settings(monkeypatch: pytest.MonkeyPatch) -> LlmSettings:
    monkeypatch.setenv("OPENROUTER_API_KEY", KEY)
    return LlmSettings(
        provider="openrouter",
        model="openai/gpt-6.1-terra",
        region="global",
        reasoning="low",
        retries=1,
    )


def test_openrouter_returns_output_usage_and_the_reported_cost(
    recorded_llm: RecordedFactory,
    openrouter_settings: LlmSettings,
    claim_list: type[BaseModel],
) -> None:
    llm, _ = recorded_llm(openrouter_settings, "openrouter-terra", 200)
    result = asyncio.run(llm.complete(PROMPT, claim_list))
    assert result.output == claim_list.model_validate(
        {"claims": ["Sejm przyjął ustawę o ochronie zwierząt."]}
    )
    usage = result.usage
    assert (usage.provider, usage.model, usage.region) == (
        "openrouter",
        "openai/gpt-6.1-terra",
        "global:Azure",  # the provider OpenRouter routed the call to
    )
    assert (usage.input_tokens, usage.output_tokens) == (78, 32)
    assert usage.cost_usd == pytest.approx(0.000238)


def test_openrouter_forces_zero_retention_no_collection_and_the_reasoning_effort(
    recorded_llm: RecordedFactory,
    openrouter_settings: LlmSettings,
    claim_list: type[BaseModel],
) -> None:
    llm, sent = recorded_llm(openrouter_settings, "openrouter-terra", 200)
    asyncio.run(llm.complete(PROMPT, claim_list))
    request = json.loads(sent[0].content)
    assert request["provider"] == {"zdr": True, "data_collection": "deny"}
    assert request["reasoning"]["effort"] == "low"
    assert request["model"] == "openai/gpt-6.1-terra"
    assert sent[0].headers["authorization"] == f"Bearer {KEY}"


def test_openrouter_zdr_can_be_turned_off_for_evaluation_but_collection_stays_denied(
    recorded_llm: RecordedFactory,
    openrouter_settings: LlmSettings,
    claim_list: type[BaseModel],
) -> None:
    settings = openrouter_settings.model_copy(update={"openrouter_zdr": False})
    llm, sent = recorded_llm(settings, "openrouter-terra", 200)
    asyncio.run(llm.complete(PROMPT, claim_list))
    request = json.loads(sent[0].content)
    assert request["provider"] == {"zdr": False, "data_collection": "deny"}


@pytest.mark.parametrize(
    ("region", "url"),
    [
        ("eu", "https://eu.openrouter.ai/api/v1/chat/completions"),
        ("global", "https://openrouter.ai/api/v1/chat/completions"),
    ],
)
def test_openrouter_region_picks_the_base_url(
    recorded_llm: RecordedFactory,
    openrouter_settings: LlmSettings,
    claim_list: type[BaseModel],
    region: str,
    url: str,
) -> None:
    settings = openrouter_settings.model_copy(update={"region": region})
    llm, sent = recorded_llm(settings, "openrouter-terra", 200)
    asyncio.run(llm.complete(PROMPT, claim_list))
    assert str(sent[0].url) == url


def test_openrouter_failure_after_retries_raises_provider_unavailable(
    recorded_llm: RecordedFactory,
    openrouter_settings: LlmSettings,
    claim_list: type[BaseModel],
) -> None:
    settings = openrouter_settings.model_copy(update={"retries": 2})
    llm, sent = recorded_llm(settings, "openrouter-terra", 503)
    with pytest.raises(ProviderUnavailableError):
        asyncio.run(llm.complete(PROMPT, claim_list))
    assert len(sent) == settings.retries


def test_openrouter_needs_the_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    with pytest.raises(ValidationError, match="OPENROUTER_API_KEY"):
        LlmSettings(provider="openrouter", region="global")


@pytest.mark.parametrize("region", ["europe-west3", "us"])
def test_openrouter_region_is_eu_or_global(
    openrouter_settings: LlmSettings, region: str
) -> None:
    with pytest.raises(ValidationError):
        LlmSettings.model_validate(
            openrouter_settings.model_dump() | {"region": region}
        )


def test_openrouter_key_never_shows_in_settings_output(
    openrouter_settings: LlmSettings,
) -> None:
    assert KEY not in repr(openrouter_settings)
    assert KEY not in str(openrouter_settings.model_dump())


def test_default_claude_haiku_5_5_sends_high_reasoning_and_records_the_upstream(
    recorded_llm: RecordedFactory,
    monkeypatch: pytest.MonkeyPatch,
    claim_list: type[BaseModel],
) -> None:
    for name in ("PROVIDER", "MODEL", "REGION", "REASONING"):
        monkeypatch.delenv(f"MERITUM_LLM_{name}", raising=False)
    monkeypatch.setenv("OPENROUTER_API_KEY", KEY)
    llm, sent = recorded_llm(LlmSettings(retries=1), "openrouter-haiku", 200)
    result = asyncio.run(llm.complete(PROMPT, claim_list))
    request = json.loads(sent[0].content)
    assert (request["model"], request["reasoning"]["effort"]) == (
        "anthropic/claude-haiku-5.5",
        "high",
    )
    assert request["provider"] == {"zdr": True, "data_collection": "deny"}
    usage = result.usage
    assert (usage.region, usage.input_tokens, usage.output_tokens) == (
        "global:Google",
        259,
        33,
    )
    assert usage.cost_usd == pytest.approx(0.0000424)
